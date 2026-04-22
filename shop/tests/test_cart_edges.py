import shutil, tempfile
from datetime import date
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from shop.models import Artist, Genre, Album

TMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TMP_MEDIA_ROOT)
class CatalogEdgesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.artist = Artist.objects.create(name="CatA")
        cls.genre = Genre.objects.create(name="CatG")

        cover = SimpleUploadedFile("c.jpg", b"\xff\xd8\xff\xd9", content_type="image/jpeg")
        # NEW: tiny fake mp3 so template can call .url safely
        preview = SimpleUploadedFile("p.mp3", b"ID3", content_type="audio/mpeg")

        cls.album = Album.objects.create(
            title="AlphaBeat",
            artist=cls.artist,
            genre=cls.genre,
            price=Decimal("5.55"),
            cover_image=cover,
            preview_clip=preview,          # <-- add this line
            release_date=date(2022, 2, 2),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP_MEDIA_ROOT, ignore_errors=True)

    def test_catalog_renders_and_search(self):
        self.assertEqual(self.client.get("/catalog/").status_code, 200)
        self.assertEqual(self.client.get("/catalog/?q=Alpha").status_code, 200)

    def test_track_catalog_and_ambient_render(self):
        self.assertEqual(self.client.get("/track_catalog/").status_code, 200)
        self.assertEqual(self.client.get("/ambient/").status_code, 200)

    def test_add_to_cart_invalid_type_is_400(self):
        r = self.client.post("/add_to_cart/foo/999/", follow=True)
        self.assertEqual(r.status_code, 400)

    def test_process_checkout_empty_cart_redirects_to_cart(self):
        r = self.client.post("/process-checkout/", follow=False)
        # should redirect to cart because cart is empty
        self.assertEqual(r.status_code, 302)
        self.assertIn("/cart", r["Location"])

    def test_process_checkout_rejects_get(self):
        r = self.client.get("/process-checkout/")
        self.assertEqual(r.status_code, 405)
