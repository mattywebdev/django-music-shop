from rest_framework import serializers
from .models import Album, Track, Artist

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = '__all__'

class AlbumSerializer(serializers.ModelSerializer):
    artist = serializers.StringRelatedField()  # uses Artist.__str__()
    genre  = serializers.StringRelatedField()  # uses Genre.__str__()
    class Meta:
        model = Album
        fields = ("id","title","artist","genre","price","release_date")

class TrackSerializer(serializers.ModelSerializer):
    artist = serializers.StringRelatedField(read_only=True)
    album = serializers.StringRelatedField(read_only=True)

    artist_id = serializers.PrimaryKeyRelatedField(
        queryset=Artist.objects.all(),
        source="artist",
        write_only=True
    )
    album_id = serializers.PrimaryKeyRelatedField(
        queryset=Album.objects.all(),
        source="album",
        write_only=True
    )

    class Meta:
        model = Track
        fields = (
            "id",
            "title",
            "artist",
            "album",
            "artist_id",
            "album_id",
            "price",
            "duration",
        )