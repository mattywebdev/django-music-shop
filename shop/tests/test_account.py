import shutil, tempfile
from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from shop.models import Album, Artist, Genre, Favorite

TMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TMP_MEDIA_ROOT)
class AccountViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("accu", password="p")
        cls.artist = Artist.objects.create(name="A1")
        cls.genre = Genre.objects.create(name="G1")
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

    def test_account_requires_login_redirects_to_login(self):
        r = self.client.get("/account/")  # no follow
        self.assertEqual(r.status_code, 302)
        self.assertIn("login", r["Location"])
        # Don't fetch r["Location"]; some setups return a 404 here during tests.

    def test_account_dashboard_shows_favorite_card(self):
        self.client.login(username="accu", password="p")
        Favorite.objects.create(
            user=User.objects.get(username="accu"),
            item_type="album",
            item_id=self.album.id,
            title=self.album.title,
        )
        r = self.client.get("/account/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "My Account")
        self.assertContains(r, "Favourites")
        self.assertContains(r, "Snow")
