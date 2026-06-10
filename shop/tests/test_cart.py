import shutil
import tempfile
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from shop.models import Album, Artist, Genre, CartItem, Favorite, Order, OrderItem

# Use a temp media dir so test files don't touch your real MEDIA_ROOT
TMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TMP_MEDIA_ROOT)
class CartFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # users & relateds
        cls.user = User.objects.create_user("u", password="p")
        cls.artist = Artist.objects.create(name="Tester Artist")
        cls.genre = Genre.objects.create(name="Test Genre")

        # Minimal JPEG bytes so ImageField is happy
        cover = SimpleUploadedFile(
            "cover.jpg",
            b"\xff\xd8\xff\xd9",     # SOI + EOI markers = minimal jpeg
            content_type="image/jpeg",
        )

        # If your Album requires preview_clip too, uncomment this and add to create(...)
        # preview = SimpleUploadedFile("clip.mp3", b"ID3", content_type="audio/mpeg")

        cls.album = Album.objects.create(
            title="A",
            artist=cls.artist,
            genre=cls.genre,
            price=Decimal("9.99"),
            cover_image=cover,
            release_date=date(2020, 1, 1),
            # preview_clip=preview,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = Client()

    def test_toggle_favorite_adds_and_removes(self):
        self.client.login(username="u", password="p")
        url = reverse("toggle_favorite", args=("album", self.album.id))
        self.client.post(url, follow=True)
        self.assertTrue(
            Favorite.objects.filter(
                user=self.user, item_type="album", item_id=self.album.id
            ).exists()
        )
        self.client.post(url, follow=True)
        self.assertFalse(
            Favorite.objects.filter(
                user=self.user, item_type="album", item_id=self.album.id
            ).exists()
        )

    def test_update_cart_all_updates_and_removes(self):
        # Add one album
        self.client.post(reverse("add_to_cart", args=("album", self.album.id)), follow=True)
        # Update qty -> 3
        self.client.post(
            reverse("update_cart_all"),
            data={f"quantity_album_{self.album.id}": "3"},
            follow=True,
        )
        s = self.client.session["cart"][f"album_{self.album.id}"]
        self.assertEqual(s["quantity"], 3)

        # Set qty -> 0 removes it
        self.client.post(
            reverse("update_cart_all"),
            data={f"quantity_album_{self.album.id}": "0"},
            follow=True,
        )
        self.assertNotIn(f"album_{self.album.id}", self.client.session["cart"])

    def test_logged_in_cart_persists_between_sessions(self):
        self.client.login(username="u", password="p")
        self.client.get(reverse("add_to_cart", args=("album", self.album.id)), follow=True)

        saved_item = CartItem.objects.get(
            user=self.user,
            item_type="album",
            item_id=self.album.id,
        )
        self.assertEqual(saved_item.quantity, 1)

        fresh_client = Client()
        fresh_client.login(username="u", password="p")
        response = fresh_client.get(reverse("cart"))

        self.assertEqual(response.status_code, 200)
        cart = fresh_client.session["cart"]
        self.assertIn(f"album_{self.album.id}", cart)
        self.assertEqual(cart[f"album_{self.album.id}"]["quantity"], 1)

    def test_checkout_creates_order_and_items(self):
        self.client.post(reverse("add_to_cart", args=("album", self.album.id)), follow=True)
        self.client.login(username="u", password="p")
        self.client.post(reverse("process_checkout"), follow=True)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertFalse(CartItem.objects.filter(user=self.user).exists())
