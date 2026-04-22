from decimal import Decimal
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Order, OrderItem, Genre, Artist, Album, Track, Ambient, Tshirt, Vinyl, Poster, Favorite
from urllib.parse import quote_plus
from django.urls import reverse

@login_required
def account_dashboard(request):
    recent_orders = request.user.orders.all()[:5]
    favs = request.user.favorites.all()[:6]

    fav_cards = []
    for f in favs:
        obj, title, image_url, price = _resolve_item(f.item_type, f.item_id)
        title = title or f.title

        fav_cards.append({
            "f": f,
            "title": title,
            "image_url": image_url,
            "price": price,
            "shop_url": _shop_url_for(f.item_type, title),
        })

    return render(
        request,
        "shop/account/dashboard.html",
        {
            "recent_orders": recent_orders,
            "fav_cards": fav_cards,
        },
    )

def _shop_url_for(item_type: str, title: str | None, item_id: int) -> str:
    t = (item_type or "").lower()

    if t == "album":
        # to top of Album Catalog:
        # return reverse("catalog")
        # or jump to a specific card anchor:
        return f"{reverse('catalog')}#album-{item_id}"

    if t == "track":
        # return reverse("track_catalog")
        return f"{reverse('track_catalog')}#track-{item_id}"

    if t in {"tshirt", "vinyl", "poster"}:
        return f"{reverse('merchandise')}?category={t}"

    if t == "ambient":
        return reverse("ambient")

    return reverse("landing_page")

def _resolve_item(item_type, item_id):
    """Return (obj, tittle, image_url, price) for listings; tolerate missing."""
    obj = title = image_url = None
    price = Decimal("0.00")

    if item_type == 'album':
        try:
            obj = Album.objects.select_related("artist").get(pk=item_id)
            title = f"{obj.title} by {obj.artist.name}"
            image_url = getattr(getattr(obj, "cover_image", None), "url", None)
            price = getattr(obj, "price", Decimal("0.00"))
        except Album.DoesNotExist:
            pass
    elif item_type == 'track':
        try:
            obj = Track.objects.select_related("album__artist").get(pk=item_id)
            title = f"{obj.title} from {obj.album.title} by {obj.album.artist.name}"
            image_url = getattr(getattr(obj.album, "cover_image", None), "url", None) if getattr(obj, "album", None) else None
            price = getattr(obj, "price", Decimal("0.00"))
        except Track.DoesNotExist:
            pass
    elif item_type == 'ambient':
        try:
            obj = Ambient.objects.select_related("artist").get(pk=item_id)
            title = f"{obj.name} by {obj.artist.name}"
            image_url = getattr(getattr(obj, "cover_image", None), "url", None) if getattr(obj, "album", None) else None
            price = getattr(obj, "price", Decimal("0.00"))
        except Ambient.DoesNotExist:
            pass
    elif item_type == 'tshirt':
        try:
            obj = Tshirt.objects.select_related("artist").get(pk=item_id)
            title = f"{obj.artist.name} T-shirt - {obj.size} ({obj.color})"
            image_url = getattr(getattr(obj, "image", None), "url", None) if getattr(obj, "album", None) else None
            price = getattr(obj, "price", Decimal("0.00"))
        except Tshirt.DoesNotExist:
            pass
    elif item_type == 'vinyl':
        try:
            obj = Vinyl.objects.select_related("artist").get(pk=item_id)
            title = f"{obj.artist.name} Vinyl - {obj.edition} ({obj.release_year})"
            image_url = getattr(getattr(obj, "image", None), "url", None) if getattr(obj, "album", None) else None
            price = getattr(obj, "price", Decimal("0.00"))
        except Vinyl.DoesNotExist:
            pass
    elif item_type == 'poster':
        try:
            obj = Poster.objects.select_related("artist").get(pk=item_id)
            title = f"{obj.artist.name} Poster - {obj.dimensions}"
            image_url = getattr(getattr(obj, "image", None), "url", None) if getattr(obj, "album", None) else None
            price = getattr(obj, "price", Decimal("0.00"))
        except Poster.DoesNotExist:
            pass
    return obj, title, image_url, price

@login_required
def order_list(request):
    orders = (Order.objects
              .filter(user=request.user)
              .prefetch_related('items')
              .order_by('-created_at'))
    return render(request, "shop/account/order_list.html", {"orders": orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.filter(user=request.user), pk=order_id)
    # If you don’t have a related_name, access via order.orderitem_set
    items = order.items.all() if hasattr(order, "items") else order.orderitem_set.all()
    return render(request, "shop/account/order_detail.html", {"order": order, "items": items})

@login_required
def favorites(request):
    favs = request.user.favorites.all()

    fav_cards = []
    for f in favs:
        _, title, image_url, price = _resolve_item(f.item_type, f.item_id)
        title = title or f.title
        fav_cards.append({
            "f": f,
            "title": title,
            "image_url": image_url,
            "price": price,
            "shop_url": _shop_url_for(f.item_type, title, f.item_id),  # pass id
        })

    return render(request, "shop/account/favorites.html", {"fav_cards": fav_cards})

ALLOWED_TYPES = {"album", "track", "tshirt", "vinyl", "poster", "ambient"}

@require_POST
@login_required(login_url='login')
def toggle_favorite(request, item_type, item_id):
    """Toggle a favorite for the current user based on URL params."""
    item_type = (item_type or "").lower()
    if item_type not in ALLOWED_TYPES:
        messages.error(request, "Invalid item.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Optional: try to resolve a nice title; fall back if missing
    title = None
    try:
        _, title, _, _ = _resolve_item(item_type, int(item_id))
    except Exception:
        pass
    title = title or f"{item_type} #{item_id}"

    fav, created = Favorite.objects.get_or_create(
        user=request.user,
        item_type=item_type,
        item_id=int(item_id),
        defaults={"title": title},
    )
    if created:
        messages.success(request, f"Added {title} to favourites.")
    else:
        fav.delete()
        messages.info(request, f"Removed {title} from favourites.")

    return redirect(request.META.get("HTTP_REFERER", "/"))