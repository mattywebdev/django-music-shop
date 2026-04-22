from django.db import models
from datetime import timedelta
from django.contrib.auth.models import User
from django.conf import settings
from decimal import Decimal
from django.contrib.auth.decorators import login_required


class Genre(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Artist(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Ambient(models.Model):
    name = models.CharField(max_length=100)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    genre = models.CharField(max_length=100)
    cover_image = models.ImageField(upload_to='ambient_covers/')
    preview_clip = models.FileField(upload_to='ambient_previews/', null=True)
    release_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Album(models.Model):
    title = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    release_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cover_image = models.ImageField(upload_to='album_covers/') # Pillow
    preview_clip = models.FileField(upload_to='audio_previews/', null=True)
    sales = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title
    
    @property
    def tracks_count(self):
        # Count the number of tracks associated with this album
        return self.tracks.count()
    
    @property
    def total_duration(self):
        # Calculate the total duration of all tracks
        total_duration = sum((track.duration for track in self.tracks.all()), timedelta())
        return total_duration
    
class Track(models.Model):
    title = models.CharField(max_length=200)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='tracks')
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    duration = models.DurationField() # duration of the track
    preview_clip = models.FileField(upload_to='track_previews/', null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.album.title}"
    
    @property
    def cover_image(self):
        # Inherit cover image from the associated album
        return self.album.cover_image
    
    @property
    def genre(self):
        # Inherit genre from the associated album
        return self.album.genre
    
    def get_price(self):
        # Use track's individual price if set; otherwise fall back to album price
        return self.price if self.price is not None else self.album.price
    
class Merchandise(models.Model):  
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)  
    price = models.DecimalField(max_digits=10, decimal_places=2)  
    image = models.ImageField(upload_to='merch_images/')  
    sales = models.PositiveIntegerField(default=0)

    class Meta:  
        abstract = True  # This prevents Django from creating a separate table for Merchandise  

class Tshirt(Merchandise):  
    size = models.CharField(max_length=10)  
    color = models.CharField(max_length=20)  

    def __str__(self):  
        return f"{self.artist.name} T-shirt - {self.size} ({self.color})"  

class Vinyl(Merchandise):  
    edition = models.CharField(max_length=50)  
    release_year = models.PositiveIntegerField()  

    def __str__(self):  
        return f"{self.artist.name} Vinyl - {self.edition} ({self.release_year})"  

class Poster(Merchandise):  
    dimensions = models.CharField(max_length=50)  

    def __str__(self):  
        return f"{self.artist.name} Poster - {self.dimensions}"  
    
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=50)
    item_id = models.IntegerField()
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    icon_url = models.URLField()

    def total_price(self):
        return self.price * self.quantity
    
class Order(models.Model):
    STATUS_CHOICES = [
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="paid")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.pk} - {self.user or 'guest'} - {self.created_at:%Y-%m-%d}"
    
class OrderItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ("album", "Album"),
        ("track", "Track"),
        ("tshirt", "T-shirt"),
        ("vinyl", "Vinyl"),
        ("poster", "Poster"),
        ("ambient", "Ambient"),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items",
                              null=True, blank=True)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    item_id = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")  # <-- add default
    )

    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.title} x{self.quantity} ({self.item_type} #{self.item_id})"
    
class Favorite(models.Model):
    ITEM_TYPE_CHOICES = [
        ("album", "Album"),
        ("track", "Track"),
        ("tshirt", "T-shirt"),
        ("vinyl", "Vinyl"),
        ("poster", "Poster"),
        ("ambient", "Ambient"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    item_id = models.PositiveIntegerField()
    title = models.CharField(max_length=255)  # denormalized for easy listing
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "item_type", "item_id")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} ♥ {self.item_type} #{self.item_id} — {self.title[:32]}"