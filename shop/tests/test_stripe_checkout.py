from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import stripe
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from shop.models import Album, Artist, CartItem, Genre, Order


@override_settings(
    STRIPE_SECRET_KEY="sk_test_example",
    STRIPE_WEBHOOK_SECRET="whsec_test_example",
    STRIPE_CURRENCY="gbp",
)
class StripeCheckoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "buyer", email="buyer@example.com", password="p"
        )
        artist = Artist.objects.create(name="Checkout Artist")
        genre = Genre.objects.create(name="Checkout Genre")
        cls.album = Album.objects.create(
            title="Authoritative Album",
            artist=artist,
            genre=genre,
            release_date=date(2026, 1, 1),
            price=Decimal("12.34"),
            cover_image="album_covers/checkout.jpg",
        )

    def setUp(self):
        self.client.login(username="buyer", password="p")

    def add_album(self):
        self.client.post(reverse("add_to_cart", args=("album", self.album.pk)))

    @staticmethod
    def stripe_session(session_id="cs_test_phase_2"):
        return SimpleNamespace(
            id=session_id,
            url=f"https://checkout.stripe.com/c/pay/{session_id}",
        )

    def test_checkout_views_require_authentication(self):
        self.client.logout()
        for method, url in (
            ("get", reverse("checkout")),
            ("post", reverse("process_checkout")),
        ):
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("login"), response["Location"])
        self.assertFalse(Order.objects.exists())

    @patch("shop.checkout_service.stripe.checkout.Session.create")
    def test_creates_pending_order_from_database_prices_and_redirects(self, create):
        create.return_value = self.stripe_session()
        self.add_album()

        session = self.client.session
        session["cart"][f"album_{self.album.pk}"]["price"] = "0.01"
        session.save()
        self.album.price = Decimal("14.25")
        self.album.save(update_fields=["price"])

        response = self.client.post(reverse("process_checkout"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], create.return_value.url)
        order = Order.objects.get()
        item = order.items.get()
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.total_amount, Decimal("14.25"))
        self.assertEqual(item.unit_price, Decimal("14.25"))
        self.assertEqual(order.stripe_checkout_session_id, "cs_test_phase_2")

        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["line_items"][0]["price_data"]["unit_amount"], 1425)
        self.assertEqual(kwargs["line_items"][0]["price_data"]["currency"], "gbp")
        self.assertEqual(
            kwargs["line_items"][0]["price_data"]["product_data"],
            {"name": "Authoritative Album"},
        )
        self.assertNotIn("price", kwargs["line_items"][0])

    @patch("shop.checkout_service.stripe.checkout.Session.create")
    def test_session_references_internal_order_and_uses_absolute_urls(self, create):
        create.return_value = self.stripe_session("cs_test_metadata")
        self.add_album()
        self.client.post(reverse("process_checkout"))

        order = Order.objects.get()
        kwargs = create.call_args.kwargs
        expected_metadata = {
            "order_id": str(order.pk),
            "user_id": str(self.user.pk),
        }
        self.assertEqual(kwargs["client_reference_id"], str(order.pk))
        self.assertEqual(kwargs["metadata"], expected_metadata)
        self.assertEqual(kwargs["payment_intent_data"]["metadata"], expected_metadata)
        self.assertEqual(kwargs["idempotency_key"], f"checkout-order-{order.pk}")
        self.assertEqual(kwargs["api_key"], "sk_test_example")
        self.assertTrue(kwargs["success_url"].startswith("http://testserver/"))
        self.assertIn("{CHECKOUT_SESSION_ID}", kwargs["success_url"])
        self.assertTrue(kwargs["cancel_url"].startswith("http://testserver/"))
        self.assertEqual(kwargs["customer_email"], "buyer@example.com")
        self.assertEqual(
            kwargs["name_collection"],
            {"individual": {"enabled": True, "optional": False}},
        )
        self.assertNotIn("shipping_address_collection", kwargs)
        self.assertNotIn("automatic_tax", kwargs)

    @patch("shop.checkout_service.stripe.checkout.Session.create")
    def test_cart_is_not_cleared_after_session_creation(self, create):
        create.return_value = self.stripe_session("cs_test_cart_kept")
        self.add_album()
        self.client.post(reverse("process_checkout"))

        self.assertIn(f"album_{self.album.pk}", self.client.session["cart"])
        self.assertTrue(
            CartItem.objects.filter(
                user=self.user, item_type="album", item_id=self.album.pk
            ).exists()
        )

    @patch("shop.checkout_service.stripe.checkout.Session.create")
    def test_stripe_failure_leaves_pending_order_and_cart(self, create):
        create.side_effect = stripe.StripeError("Stripe is unavailable")
        self.add_album()

        response = self.client.post(reverse("process_checkout"))

        self.assertRedirects(response, reverse("checkout"), fetch_redirect_response=False)
        order = Order.objects.get()
        self.assertEqual(order.status, "pending")
        self.assertIsNone(order.stripe_checkout_session_id)
        self.assertIn(f"album_{self.album.pk}", self.client.session["cart"])

    @patch("shop.checkout_service.stripe.checkout.Session.create")
    def test_return_pages_never_mark_order_paid(self, create):
        create.return_value = self.stripe_session("cs_test_unpaid")
        self.add_album()
        self.client.post(reverse("process_checkout"))
        order = Order.objects.get()

        self.client.get(reverse("success") + "?session_id=cs_test_unpaid")
        self.client.get(reverse("checkout_cancelled"))

        order.refresh_from_db()
        self.assertEqual(order.status, "pending")
        self.assertIsNone(order.paid_at)
        self.assertFalse(Order.objects.filter(status="paid").exists())
