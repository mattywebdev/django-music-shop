import shutil, tempfile
from datetime import date
from decimal import Decimal
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from shop.models import Artist, Genre, Album

TMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TMP_MEDIA_ROOT)
class MiscViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        artist = Artist.objects.create(name="MerchArtist")
        genre = Genre.objects.create(name="MerchGenre")
        cover = SimpleUploadedFile("c.jpg", b"\xff\xd8\xff\xd9", content_type="image/jpeg")
        cls.album = Album.objects.create(
            title="Z",
            artist=artist,
            genre=genre,
            price=Decimal("7.00"),
            cover_image=cover,
            release_date=date(2021, 1, 1),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP_MEDIA_ROOT, ignore_errors=True)

    def test_merch_all_and_categories(self):
        # These should render even with zero products
        for cat in ("all", "tshirt", "vinyl", "poster"):
            r = self.client.get(f"/merchandise/?category={cat}")
            self.assertEqual(r.status_code, 200)

    def test_remove_from_cart_and_success(self):
        self.client.post(f"/add_to_cart/album/{self.album.id}/", follow=True)
        self.client.get(f"/remove_from_cart/album/{self.album.id}/", follow=True)
        s = self.client.get("/success/")
        self.assertEqual(s.status_code, 200)