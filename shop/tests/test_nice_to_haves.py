# shop/tests/test_nice_to_haves.py
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from shop.models import Album, Artist, Genre


class NiceToHavesTests(TestCase):
    def setUp(self):
        self.artist = Artist.objects.create(name="A1")
        self.genre = Genre.objects.create(name="G1")

    # 1) Add-to-cart increments quantity on duplicate adds
    def test_add_to_cart_increments_quantity(self):
        album = Album.objects.create(
            title="Snow",
            price=Decimal("12.50"),
            artist=self.artist,
            genre=self.genre,
            release_date=date(2024, 1, 1),
        )

        url = reverse("add_to_cart", args=("album", album.id))
        # Add twice
        self.client.get(url, follow=True)
        self.client.get(url, follow=True)

        session = self.client.session
        cart = session.get("cart", {})
        key = f"album_{album.id}"

        self.assertIn(key, cart)
        self.assertEqual(cart[key]["quantity"], 2)
        self.assertEqual(session.get("total_quantity"), 2)

    # 2) Removing items updates totals
    def test_remove_from_cart_updates_totals(self):
        a1 = Album.objects.create(
            title="A",
            price=Decimal("10.00"),
            artist=self.artist,
            genre=self.genre,
            release_date=date(2024, 1, 1),
        )
        a2 = Album.objects.create(
            title="B",
            price=Decimal("5.00"),
            artist=self.artist,
            genre=self.genre,
            release_date=date(2024, 1, 2),
        )

        # Add A twice, B once (total 3 items)
        self.client.get(reverse("add_to_cart", args=("album", a1.id)), follow=True)
        self.client.get(reverse("add_to_cart", args=("album", a1.id)), follow=True)
        self.client.get(reverse("add_to_cart", args=("album", a2.id)), follow=True)

        # Remove B; total should drop to 2, and key for B gone
        self.client.get(reverse("remove_from_cart", args=("album", a2.id)), follow=True)

        session = self.client.session
        cart = session.get("cart", {})
        self.assertNotIn(f"album_{a2.id}", cart)
        self.assertEqual(session.get("total_quantity"), 2)

    # 3) Albums API pagination & ordering edge cases
    def test_albums_api_pagination_and_ordering(self):
        # ... create 13 albums as you already do ...

        r1 = self.client.get(reverse("albums_api") + "?ordering=-price")
        self.assertEqual(r1.status_code, 200)
        data1 = r1.json()

        # Accept both shapes: paginated dict or raw list
        if isinstance(data1, dict) and "results" in data1:
            results1 = data1["results"]
            total_count = data1.get("count", len(results1))
        else:
            results1 = data1
            total_count = len(results1)

        self.assertEqual(total_count, 13)

        # First page should have at most 12
        self.assertLessEqual(len(results1), 12)
        prices_page1 = [Decimal(item["price"]) for item in results1]
        self.assertTrue(all(prices_page1[i] >= prices_page1[i+1] for i in range(len(prices_page1)-1)))

        # Page 2 (if pagination is active) should contain the remainder
        r2 = self.client.get(reverse("albums_api") + "?ordering=-price&page=2")
        if r2.status_code == 200:
            data2 = r2.json()
            if isinstance(data2, dict) and "results" in data2:
                self.assertEqual(len(data2["results"]), 1)

    # 4) Empty-state pages (favorites/orders) sanity checks
    def test_favorites_empty_state(self):
        # Must be logged in to view page
        self.client.force_login(
            # Create a basic user
            __import__("django.contrib.auth.models").contrib.auth.models.User.objects.create_user(
                username="u1", password="pw"
            )
        )
        r = self.client.get(reverse("favorites"))
        self.assertEqual(r.status_code, 200)
        # Page renders but no "Remove ♥" buttons (no cards)
        self.assertNotContains(r, "Remove ♥")

    def test_orders_list_empty_state(self):
        self.client.force_login(
            __import__("django.contrib.auth.models").contrib.auth.models.User.objects.create_user(
                username="u2", password="pw"
            )
        )
        r = self.client.get(reverse("order_list"))
        self.assertEqual(r.status_code, 200)
        # No rows linking to an order detail when empty
        self.assertNotContains(r, "/account/orders/")
