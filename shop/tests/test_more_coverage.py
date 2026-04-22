from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from shop.models import Artist, Genre, Album, Order, OrderItem

def img(name="x.jpg"):
    return SimpleUploadedFile(name, b"\x47\x49\x46", content_type="image/jpeg")

class MoreCoverageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.artist = Artist.objects.create(name="AA")
        cls.genre1 = Genre.objects.create(name="G1")
        cls.genre2 = Genre.objects.create(name="G2")
        cls.album1 = Album.objects.create(
            title="Snow",
            artist=cls.artist,
            genre=cls.genre1,
            price=Decimal("12.50"),
            release_date=date(2024, 1, 1),
            cover_image=img("a1.jpg"),
        )
        cls.album2 = Album.objects.create(
            title="Rain",
            artist=cls.artist,
            genre=cls.genre2,
            price=Decimal("9.99"),
            release_date=date(2024, 2, 1),
            cover_image=img("a2.jpg"),
        )
        cls.user1 = User.objects.create_user("u1", password="pw")
        cls.user2 = User.objects.create_user("u2", password="pw")

    # --- Account/orders edges ---
    def test_order_detail_only_owner_can_view(self):
        order = Order.objects.create(user=self.user1, status="paid", total_amount=Decimal("12.50"))
        OrderItem.objects.create(order=order, item_type="album", item_id=self.album1.id,
                                 title=self.album1.title, unit_price=self.album1.price, quantity=1)
        self.client.login(username="u2", password="pw")
        r = self.client.get(reverse("order_detail", args=[order.pk]))
        # Your view filters by request.user, so non-owner should 404
        self.assertEqual(r.status_code, 404)

    def test_favorites_requires_login_redirect(self):
        r = self.client.get(reverse("favorites"), follow=False)
        self.assertIn(r.status_code, (302, 301))  # redirected to login

    # --- API edges ---
    def test_api_ping_ok(self):
        r = self.client.get(reverse("api_ping"))
        self.assertEqual(r.status_code, 200)
        self.assertJSONEqual(r.content, {"ok": True})

    def test_albums_api_filtered_by_genre(self):
        url = reverse("albums_api") + f"?genre={self.genre1.id}"
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(any(a["title"] == "Snow" for a in data))
        self.assertFalse(any(a["title"] == "Rain" for a in data))

    def test_tracks_api_invalid_page_404(self):
        url = reverse("tracks_api") + "?page=999"
        r = self.client.get(url)
        self.assertEqual(r.status_code, 404)
        self.assertIn("Invalid page", r.json().get("detail", ""))
