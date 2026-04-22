import shutil, tempfile
from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from shop.templatetags.custom_filters import instance_of, is_favorite
from shop.models import Album, Artist, Genre, Favorite

TMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TMP_MEDIA_ROOT)
class FiltersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("u", password="p")
        artist = Artist.objects.create(name="N")
        genre = Genre.objects.create(name="G")
        cover = SimpleUploadedFile("c.jpg", b"\xff\xd8\xff\xd9", content_type="image/jpeg")
        cls.album = Album.objects.create(
            title="T",
            artist=artist,
            genre=genre,
            price=Decimal("5.00"),
            cover_image=cover,
            release_date=date(2022, 1, 1),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP_MEDIA_ROOT, ignore_errors=True)

    def test_instance_of_modelname(self):
        self.assertTrue(instance_of(self.album, "Album"))
        self.assertTrue(instance_of(self.album, "album"))

    def test_is_favorite_true_false(self):
        self.assertFalse(is_favorite(self.user, "album", self.album.id))
        Favorite.objects.create(user=self.user, item_type="album", item_id=self.album.id, title="T")
        self.assertTrue(is_favorite(self.user, "album", self.album.id))
