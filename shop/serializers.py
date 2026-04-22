from rest_framework import serializers
from .models import Album, Track

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
    artist = serializers.StringRelatedField()
    album = serializers.StringRelatedField()
    class Meta:
        model = Track
        fields = ("id", "title", "artist", "album", "price", "duration")