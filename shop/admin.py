from django.contrib import admin
from .models import Genre, Artist, Album, Track, Tshirt, Vinyl, Poster, Ambient, Order, OrderItem, Favorite

# Register Genre and Artist normally
admin.site.register(Genre)
admin.site.register(Artist)
admin.site.register(Tshirt)
admin.site.register(Vinyl)
admin.site.register(Poster)
admin.site.register(Ambient)

# Inline setup for adding Tracks directly in the Album admin page
class TrackInLine(admin.TabularInline):
    model = Track
    extra = 1  # Number of extra forms to show for new tracks

# Register Album with the inline Track setup
@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    inlines = [TrackInLine]

# Custom Track admin setup
@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'album', 'get_price', 'duration', 'artist', 'genre')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username",)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "item_type", "item_id", "title", "quantity", "unit_price")
    list_filter = ("item_type",)
    search_fields = ("title",)

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "item_type", "item_id", "title", "created_at")
    list_filter = ("item_type", "created_at")
    search_fields = ("title", "user__username")