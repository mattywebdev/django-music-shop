import shutil
import tempfile
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from shop.entitlement_service import ensure_order_entitlements
from shop.models import (
    Album,
    Artist,
    DigitalEntitlement,
    Genre,
    Order,
    OrderItem,
    Poster,
    Track,
)
from shop.webhook_service import process_checkout_payment_event


PRIVATE_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(PRIVATE_MEDIA_ROOT=PRIVATE_MEDIA_ROOT, STRIPE_CURRENCY="gbp")
class DigitalEntitlementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user("owner", password="p")
        cls.other_user = User.objects.create_user("other", password="p")
        cls.artist = Artist.objects.create(name="Download Artist")
        cls.genre = Genre.objects.create(name="Download Genre")
        cls.album = Album.objects.create(
            title="Purchased Album",
            artist=cls.artist,
            genre=cls.genre,
            release_date=date(2026, 1, 1),
            price=Decimal("9.99"),
            cover_image="album_covers/purchased.jpg",
        )
        cls.other_album = Album.objects.create(
            title="Unrelated Album",
            artist=cls.artist,
            genre=cls.genre,
            release_date=date(2026, 1, 2),
            price=Decimal("8.99"),
            cover_image="album_covers/unrelated.jpg",
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(PRIVATE_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.track_one = Track.objects.create(
            title="Owned Track One",
            album=self.album,
            artist=self.artist,
            duration=timedelta(minutes=3),
            price=Decimal("1.25"),
            download_file=SimpleUploadedFile("owned-one.mp3", b"owned-one"),
        )
        self.track_two = Track.objects.create(
            title="Owned Track Two",
            album=self.album,
            artist=self.artist,
            duration=timedelta(minutes=4),
            price=Decimal("1.50"),
            download_file=SimpleUploadedFile("owned-two.mp3", b"owned-two"),
        )
        self.unrelated_track = Track.objects.create(
            title="Unrelated Track",
            album=self.other_album,
            artist=self.artist,
            duration=timedelta(minutes=2),
            price=Decimal("0.99"),
            download_file=SimpleUploadedFile("unrelated.mp3", b"unrelated"),
        )
        self.order_counter = 0

    def make_order(self, item_type, item_id, amount=Decimal("9.99"), status="pending"):
        self.order_counter += 1
        order = Order.objects.create(
            user=self.owner,
            status=status,
            total_amount=amount,
            stripe_checkout_session_id=f"cs_test_entitlement_{self.order_counter}",
        )
        item = OrderItem.objects.create(
            order=order,
            item_type=item_type,
            item_id=item_id,
            title=f"Purchased {item_type}",
            quantity=1,
            unit_price=amount,
        )
        return order, item

    def paid_event(self, order, event_id):
        return {
            "id": event_id,
            "type": "checkout.session.completed",
            "data": {"object": {
                "id": order.stripe_checkout_session_id,
                "client_reference_id": str(order.pk),
                "metadata": {
                    "order_id": str(order.pk),
                    "user_id": str(self.owner.pk),
                },
                "mode": "payment",
                "payment_status": "paid",
                "currency": "gbp",
                "amount_total": int(order.total_amount * 100),
                "payment_intent": f"pi_test_order_{order.pk}",
            }},
        }

    def grant_via_webhook(self, item_type, item_id, event_id):
        order, item = self.make_order(item_type, item_id)
        process_checkout_payment_event(self.paid_event(order, event_id))
        order.refresh_from_db()
        return order, item

    def test_paid_album_creates_one_album_entitlement(self):
        order, item = self.grant_via_webhook("album", self.album.pk, "evt_album")
        entitlement = DigitalEntitlement.objects.get()
        self.assertEqual(order.status, "paid")
        self.assertEqual(entitlement.user, self.owner)
        self.assertEqual(entitlement.order_item, item)
        self.assertEqual(entitlement.product_type, "album")
        self.assertEqual(entitlement.product_id, self.album.pk)

    def test_paid_track_creates_one_track_entitlement(self):
        _, item = self.grant_via_webhook("track", self.track_one.pk, "evt_track")
        entitlement = DigitalEntitlement.objects.get()
        self.assertEqual(entitlement.order_item, item)
        self.assertEqual(entitlement.product_type, "track")
        self.assertEqual(entitlement.product_id, self.track_one.pk)

    def test_merchandise_does_not_create_entitlement(self):
        poster = Poster.objects.create(
            artist=self.artist,
            price=Decimal("9.99"),
            image="merch_images/poster.jpg",
            dimensions="A3",
        )
        self.grant_via_webhook("poster", poster.pk, "evt_poster")
        self.assertFalse(DigitalEntitlement.objects.exists())

    def test_pending_order_cannot_grant_or_use_entitlement(self):
        order, item = self.make_order("track", self.track_one.pk)
        self.assertEqual(ensure_order_entitlements(order), [])
        entitlement = DigitalEntitlement.objects.create(
            user=self.owner,
            order=order,
            order_item=item,
            product_type="track",
            product_id=self.track_one.pk,
        )
        self.client.login(username="owner", password="p")
        response = self.client.get(reverse(
            "download_track", args=(entitlement.public_id, self.track_one.pk)
        ))
        self.assertEqual(response.status_code, 404)

    def test_duplicate_webhook_does_not_duplicate_entitlement(self):
        order, _ = self.make_order("album", self.album.pk)
        event = self.paid_event(order, "evt_duplicate_entitlement")
        process_checkout_payment_event(event)
        process_checkout_payment_event(event)
        self.assertEqual(DigitalEntitlement.objects.count(), 1)

    def test_repeated_verified_event_repairs_missing_entitlement_without_duplicates(self):
        order, _ = self.make_order("album", self.album.pk)
        event = self.paid_event(order, "evt_repair_entitlement")
        process_checkout_payment_event(event)
        DigitalEntitlement.objects.all().delete()
        process_checkout_payment_event(event)
        self.assertEqual(DigitalEntitlement.objects.count(), 1)

    def test_purchase_library_contains_only_current_users_entitlements(self):
        self.grant_via_webhook("track", self.track_one.pk, "evt_library")
        self.client.login(username="owner", password="p")
        response = self.client.get(reverse("purchase_library"))
        self.assertContains(response, "Owned Track One")

        self.client.logout()
        self.client.login(username="other", password="p")
        response = self.client.get(reverse("purchase_library"))
        self.assertNotContains(response, "Owned Track One")

    def test_anonymous_download_is_denied(self):
        _, item = self.grant_via_webhook("track", self.track_one.pk, "evt_anonymous")
        entitlement = item.digital_entitlement
        response = self.client.get(reverse(
            "download_track", args=(entitlement.public_id, self.track_one.pk)
        ))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_different_authenticated_user_is_denied(self):
        _, item = self.grant_via_webhook("track", self.track_one.pk, "evt_other_user")
        entitlement = item.digital_entitlement
        self.client.login(username="other", password="p")
        response = self.client.get(reverse(
            "download_track", args=(entitlement.public_id, self.track_one.pk)
        ))
        self.assertEqual(response.status_code, 404)

    def test_owner_of_paid_entitlement_can_stream_attachment(self):
        _, item = self.grant_via_webhook("track", self.track_one.pk, "evt_owner")
        entitlement = item.digital_entitlement
        self.client.login(username="owner", password="p")
        response = self.client.get(reverse(
            "download_track", args=(entitlement.public_id, self.track_one.pk)
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"owned-one")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(
            self.track_one.download_file.name.rsplit("/", 1)[-1],
            response["Content-Disposition"],
        )

    def test_inactive_entitlement_is_denied(self):
        _, item = self.grant_via_webhook("track", self.track_one.pk, "evt_inactive")
        entitlement = item.digital_entitlement
        entitlement.is_active = False
        entitlement.save(update_fields=["is_active"])
        self.client.login(username="owner", password="p")
        response = self.client.get(reverse(
            "download_track", args=(entitlement.public_id, self.track_one.pk)
        ))
        self.assertEqual(response.status_code, 404)

    def test_album_entitlement_only_allows_tracks_from_that_album(self):
        _, item = self.grant_via_webhook("album", self.album.pk, "evt_album_scope")
        entitlement = item.digital_entitlement
        self.client.login(username="owner", password="p")
        allowed = self.client.get(reverse(
            "download_track", args=(entitlement.public_id, self.track_two.pk)
        ))
        denied = self.client.get(reverse(
            "download_track", args=(entitlement.public_id, self.unrelated_track.pk)
        ))
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(denied.status_code, 404)

    def test_standalone_track_entitlement_only_allows_that_track(self):
        _, item = self.grant_via_webhook("track", self.track_one.pk, "evt_track_scope")
        entitlement = item.digital_entitlement
        self.client.login(username="owner", password="p")
        allowed = self.client.get(reverse(
            "download_track", args=(entitlement.public_id, self.track_one.pk)
        ))
        denied = self.client.get(reverse(
            "download_track", args=(entitlement.public_id, self.track_two.pk)
        ))
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(denied.status_code, 404)

    def test_arbitrary_path_cannot_be_supplied_to_download_route(self):
        _, item = self.grant_via_webhook("track", self.track_one.pk, "evt_path")
        entitlement = item.digital_entitlement
        self.client.login(username="owner", password="p")
        response = self.client.get(
            f"/account/purchases/{entitlement.public_id}/tracks/../download/"
        )
        self.assertEqual(response.status_code, 404)

    def test_success_page_does_not_create_entitlement(self):
        self.make_order("album", self.album.pk)
        self.client.login(username="owner", password="p")
        response = self.client.get(reverse("success"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(DigitalEntitlement.objects.exists())
