import shutil, tempfile
from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from shop.models import Artist, Genre, Album, Favorite, Order, OrderItem

TMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TMP_MEDIA_ROOT)
class AccountPagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("acc2", password="p")
        cls.artist = Artist.objects.create(name="FavArtist")
        cls.genre = Genre.objects.create(name="FavGenre")
        cover = SimpleUploadedFile("c.jpg", b"\xff\xd8\xff\xd9", content_type="image/jpeg")
        cls.album = Album.objects.create(
            title="Snow",
            artist=cls.artist,
            genre=cls.genre,
            price=Decimal("12.50"),
            cover_image=cover,
            release_date=date(2024, 1, 1),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = Client()
        self.client.login(username="acc2", password="p")

    def test_favourites_page_lists_cards(self):
        Favorite.objects.create(user=User.objects.get(username="acc2"),
                                item_type="album", item_id=self.album.id, title=self.album.title)
        r = self.client.get("/account/favorites/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Favourites")
        self.assertContains(r, "Snow")
        # Button/form present:
        self.assertContains(r, "Remove ♥")

    def test_orders_list_shows_order_and_item(self):
        order = Order.objects.create(user=User.objects.get(username="acc2"),
                                     status="paid", total_amount=Decimal("12.50"))
        OrderItem.objects.create(order=order, item_type="album",
                                 item_id=self.album.id, title=self.album.title,
                                 unit_price=Decimal("12.50"), quantity=1)
        r = self.client.get("/account/orders/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, f"#{order.pk}")
        self.assertContains(r, "Snow")
