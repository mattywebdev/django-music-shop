from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, override_settings

from shop.models import Album, Artist, Genre, Order, StripeEvent, Track
from shop.product_catalog import resolve_product, to_minor_units


class PaymentConfigurationTests(TestCase):
    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example",
        STRIPE_WEBHOOK_SECRET="whsec_example",
        STRIPE_CURRENCY="gbp",
    )
    def test_stripe_settings_support_test_mode_environment_values(self):
        from django.conf import settings

        self.assertTrue(settings.STRIPE_SECRET_KEY.startswith("sk_test_"))
        self.assertTrue(settings.STRIPE_WEBHOOK_SECRET.startswith("whsec_"))
        self.assertEqual(settings.STRIPE_CURRENCY, "gbp")


class PaymentModelTests(TestCase):
    def test_new_order_defaults_to_pending(self):
        order = Order.objects.create()
        self.assertEqual(order.status, "pending")
        self.assertIsNone(order.paid_at)

    def test_stripe_event_ids_are_unique(self):
        StripeEvent.objects.create(event_id="evt_test_1", event_type="checkout.session.completed")
        with self.assertRaises(IntegrityError):
            StripeEvent.objects.create(event_id="evt_test_1", event_type="checkout.session.completed")


class ProductResolutionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.artist = Artist.objects.create(name="Test Artist")
        cls.genre = Genre.objects.create(name="Test Genre")
        cls.album = Album.objects.create(
            title="Database Album",
            artist=cls.artist,
            genre=cls.genre,
            release_date=date(2026, 1, 1),
            price=Decimal("12.34"),
            cover_image="album_covers/test.jpg",
        )
        cls.track_with_price = Track.objects.create(
            title="Priced Track",
            album=cls.album,
            artist=cls.artist,
            duration=timedelta(minutes=3),
            price=Decimal("1.25"),
        )
        cls.track_with_fallback = Track.objects.create(
            title="Fallback Track",
            album=cls.album,
            artist=cls.artist,
            duration=timedelta(minutes=4),
            price=None,
        )

    def test_resolver_reads_authoritative_database_price(self):
        resolved = resolve_product("album", self.album.pk)
        self.assertEqual(resolved.title, "Database Album")
        self.assertEqual(resolved.unit_price, Decimal("12.34"))

    def test_track_resolver_uses_individual_price(self):
        resolved = resolve_product("track", self.track_with_price.pk)
        self.assertEqual(resolved.unit_price, Decimal("1.25"))

    def test_track_resolver_falls_back_to_album_price(self):
        resolved = resolve_product("track", self.track_with_fallback.pk)
        self.assertEqual(resolved.unit_price, Decimal("12.34"))

    def test_resolver_rejects_unknown_or_missing_products(self):
        with self.assertRaises(ValidationError):
            resolve_product("unknown", 1)
        with self.assertRaises(ValidationError):
            resolve_product("album", 999999)

    def test_gbp_minor_unit_conversion_never_uses_float(self):
        self.assertEqual(to_minor_units(Decimal("12.34")), 1234)
        self.assertEqual(to_minor_units(Decimal("0.01")), 1)

    def test_minor_unit_conversion_rejects_fractional_pence(self):
        with self.assertRaises(ValidationError):
            to_minor_units(Decimal("1.001"))
