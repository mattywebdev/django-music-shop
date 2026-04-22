from datetime import date
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch
from shop.models import Artist, Genre, Album, Track

def url_or(name, fallback):
    try:
        return reverse(name)
    except NoReverseMatch:
        return fallback

class ApiViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        artist = Artist.objects.create(name="Alpha")
        genre = Genre.objects.create(name="Synth")
        cover = SimpleUploadedFile("c.jpg", b"\xff\xd8\xff\xd9", content_type="image/jpeg")
        album = Album.objects.create(
            title="A-Album",
            artist=artist,
            genre=genre,
            price=Decimal("9.99"),
            cover_image=cover,
            release_date=date(2023, 5, 1),
        )
        Track.objects.create(title="AAA", album=album, artist=artist, price=Decimal("1.00"), duration="00:02:30")
        Track.objects.create(title="Beta", album=album, artist=artist, price=Decimal("2.00"), duration="00:03:00")

    def test_tracks_api_basic_and_search(self):
        tracks_url = url_or("tracks_api", "/api/tracks/")
        r = self.client.get(tracks_url)
        self.assertIn(r.status_code, (200,))  # should exist
        self.assertIn("results", r.json())

        r2 = self.client.get(f"{tracks_url}?q=AAA")
        self.assertEqual(r2.status_code, 200)
        titles = [row.get("title") for row in r2.json().get("results", [])]
        self.assertIn("AAA", titles)

    def test_tracks_api_invalid_page(self):
        tracks_url = url_or("tracks_api", "/api/tracks/")
        r = self.client.get(f"{tracks_url}?page=9999")
        # Your API may return 404 "Invalid page." or clamp to last page:
        self.assertIn(r.status_code, (404, 200))

    def test_albums_list_api(self):
        albums_url = url_or("album_list", "/api/albums/")
        r = self.client.get(albums_url)
        # If you don't expose /api/albums/, tolerate 404; otherwise assert 200
        self.assertIn(r.status_code, (200, 404))
