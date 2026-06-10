from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from .serializers import ProductSerializer
from .models import (
    Album, Track, Tshirt, Vinyl, Poster, Ambient,
    Order, OrderItem, Genre, Artist, Favorite, CartItem,
)
# If you keep the DRF view below, these are needed:
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.paginator import Paginator

def _safe_file_url(filefield, default=""):
    try:
        if filefield:
            return filefield.url
    except Exception:
        pass
    return default

def api_ping(request): return JsonResponse({"ok": True})


def _wants_json(request):
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("accept", "")
    )


def _normalise_cart(cart):
    total_qty = 0
    total_price = Decimal("0.00")

    for key, item in list((cart or {}).items()):
        try:
            quantity = max(0, int(item.get("quantity", 1)))
        except (TypeError, ValueError):
            quantity = 0

        if quantity <= 0:
            del cart[key]
            continue

        price = Decimal(str(item.get("price", "0")))
        line_total = price * quantity
        item["quantity"] = quantity
        item["total_price"] = float(line_total)
        total_qty += quantity
        total_price += line_total

    return total_qty, total_price


def _cart_key(item_type, item_id):
    return f"{item_type}_{item_id}"


def _cart_entry_from_item(cart_item):
    total_price = cart_item.price * cart_item.quantity
    return {
        "title": cart_item.title,
        "price": str(cart_item.price),
        "quantity": cart_item.quantity,
        "total_price": float(total_price),
        "icon_url": cart_item.icon_url,
        "type": cart_item.item_type,
        "id": cart_item.item_id,
    }


def load_user_cart_to_session(request):
    if not getattr(request.user, "is_authenticated", False):
        return request.session.get("cart", {}) or {}

    cart = {
        _cart_key(item.item_type, item.item_id): _cart_entry_from_item(item)
        for item in CartItem.objects.filter(user=request.user)
    }
    total_qty, total_price = _normalise_cart(cart)
    request.session["cart"] = cart
    request.session["total_quantity"] = total_qty
    request.session["cart_total_price"] = f"{total_price:.2f}"
    request.session.modified = True
    return cart


def ensure_session_cart(request):
    cart = request.session.get("cart", {}) or {}
    if cart or not getattr(request.user, "is_authenticated", False):
        return cart
    return load_user_cart_to_session(request)


def save_session_cart_to_user(request):
    if not getattr(request.user, "is_authenticated", False):
        return

    cart = request.session.get("cart", {}) or {}
    CartItem.objects.filter(user=request.user).delete()

    rows = []
    for key, item in cart.items():
        item_type = item.get("type")
        item_id = item.get("id")

        if not (item_type and item_id) and "_" in key:
            item_type, raw_id = key.split("_", 1)
            item_id = int(raw_id) if raw_id.isdigit() else None

        if not (item_type and item_id):
            continue

        rows.append(CartItem(
            user=request.user,
            item_type=item_type,
            item_id=int(item_id),
            title=item.get("title") or "Item",
            price=Decimal(str(item.get("price", "0"))),
            quantity=max(1, int(item.get("quantity", 1) or 1)),
            icon_url=item.get("icon_url") or "",
        ))

    if rows:
        CartItem.objects.bulk_create(rows)


def merge_session_cart_into_user(request):
    if not getattr(request.user, "is_authenticated", False):
        return

    session_cart = request.session.get("cart", {}) or {}

    for key, item in session_cart.items():
        item_type = item.get("type")
        item_id = item.get("id")

        if not (item_type and item_id) and "_" in key:
            item_type, raw_id = key.split("_", 1)
            item_id = int(raw_id) if raw_id.isdigit() else None

        if not (item_type and item_id):
            continue

        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            item_type=item_type,
            item_id=int(item_id),
            defaults={
                "title": item.get("title") or "Item",
                "price": Decimal(str(item.get("price", "0"))),
                "quantity": 0,
                "icon_url": item.get("icon_url") or "",
            },
        )
        cart_item.title = item.get("title") or cart_item.title
        cart_item.price = Decimal(str(item.get("price", cart_item.price)))
        cart_item.icon_url = item.get("icon_url") or cart_item.icon_url
        cart_item.quantity += max(1, int(item.get("quantity", 1) or 1))
        cart_item.save()

    load_user_cart_to_session(request)


def _cart_payload(request, message="Cart updated."):
    cart = ensure_session_cart(request)
    total_qty, total_price = _normalise_cart(cart)
    request.session["cart"] = cart
    request.session["total_quantity"] = total_qty
    request.session.modified = True
    save_session_cart_to_user(request)

    total_price_text = f"{total_price:.2f}"
    context = {
        "cart_count": total_qty,
        "cart_total_price": total_price_text,
    }

    return {
        "ok": True,
        "message": message,
        "cart_count": total_qty,
        "total_quantity": total_qty,
        "cart_total_price": total_price_text,
        "total_price": total_price_text,
        "items": {
            key: {
                "quantity": item.get("quantity", 1),
                "price": str(item.get("price", "0")),
                "total_price": f"{Decimal(str(item.get('total_price', '0'))):.2f}",
            }
            for key, item in cart.items()
        },
        "cart_dropdown_html": render_to_string(
            "partials/cart_dropdown.html",
            context,
            request=request,
        ),
    }


def about(request):
    return render(request, 'shop/about.html')

@api_view(['GET'])
def album_list(request):
    artist_id = request.GET.get('artist', None)
    genre_id = request.GET.get('genre', None)

    albums = Album.objects.all()
    if artist_id:
        albums = albums.filter(artist_id=artist_id)
    if genre_id:
        albums = albums.filter(genre_id=genre_id)

    serializer = ProductSerializer(albums, many=True)
    return Response(serializer.data)

def logoutUser(request):
    logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"Account created for {username}! You can now log in.", extra_tags="auth")
            return redirect('login')
    else:
         form = UserCreationForm()
    return render(request, 'shop/register.html', {'form': form})

def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            merge_session_cart_into_user(request)
            return redirect('landing_page')
        else:
            messages.info(request, 'Username OR password is incorrect', extra_tags="auth")
    auth_messages = [
        message for message in messages.get_messages(request)
        if 'auth' in message.tags
    ]
    return render(request, 'shop/login.html', {'auth_messages': auth_messages})


def catalog(request):
    q = request.GET.get("q")
    genre = request.GET.get("genre")
    albums = (
        Album.objects.select_related("artist","genre")
        .prefetch_related(Prefetch("tracks", queryset=Track.objects.only("id","album_id")))
        .annotate(tracks_count_db=Count("tracks"))
    )
    if q:
        albums = albums.filter(Q(title__icontains=q) | Q(artist__name__icontains=q))
    if genre and genre.isdigit():
        albums = albums.filter(genre_id=int(genre))
    return render(request, "shop/catalog.html", {"albums": albums, "q": q})

def ambient(request):
    ambients = Ambient.objects.all()
    return render(request, 'shop/ambient.html', {'ambients':ambients})

def add_to_cart(request, item_type, item_id):
    item_title = None
    item_price = None
    icon_url = None

    if item_type == 'album':
        item = get_object_or_404(Album, id=item_id)
        item_title = item.title
        item_price = item.price
        icon_url = _safe_file_url(getattr(item, "cover_image", None))
    elif item_type == 'tshirt':
        item = get_object_or_404(Tshirt, id=item_id)
        item_title = str(item)
        item_price = item.price
        icon_url = _safe_file_url(getattr(item, "image", None))
    elif item_type == 'vinyl':
        item = get_object_or_404(Vinyl, id=item_id)
        item_title = str(item)
        item_price = item.price
        icon_url = _safe_file_url(getattr(item, "image", None))
    elif item_type == 'poster':
        item = get_object_or_404(Poster, id=item_id)
        item_title = str(item)
        item_price = item.price
        icon_url = _safe_file_url(getattr(item, "image", None))
    elif item_type == 'track':
        item = get_object_or_404(Track, id=item_id)
        item_title = item.title
        item_price = item.price
        # prefer the album’s cover
        icon_url = _safe_file_url(getattr(getattr(item, "album", None), "cover_image", None))
    elif item_type == 'ambient':
        item = get_object_or_404(Ambient, id=item_id)
        item_title = str(item)
        item_price = item.price
        icon_url = _safe_file_url(getattr(item, "cover_image", None))
    else:
        return HttpResponse("Invalid item type", status=400)

    cart = ensure_session_cart(request)
    item_key = f"{item_type}_{item_id}"

    if item_key in cart:
        cart[item_key]['quantity'] += 1
        # (optional) if you want to refresh icon/price when re-adding:
        cart[item_key]['icon_url'] = cart[item_key].get('icon_url') or icon_url
        cart[item_key]['price'] = str(item_price)
    else:
        cart[item_key] = {
            'title': item_title,
            'price': str(item_price),
            'quantity': 1,
            'total_price': float(item_price),
            'icon_url': icon_url,      # << will be a real URL or placeholder
            'type': item_type,
            'id': item_id,
        }

    request.session['cart'] = cart
    request.session.modified = True
    payload = _cart_payload(request, f"{item_title} added to your cart.")

    messages.success(request, f"{item_title} added to your cart.")
    if _wants_json(request):
        return JsonResponse(payload)

    return redirect(request.META.get('HTTP_REFERER', 'landing_page'))


def cart_view(request):
    cart = ensure_session_cart(request)
    total_price = Decimal('0.00')
    total_quantity = 0
    for it in cart.values():
        q = int(it.get('quantity', 1))
        p = Decimal(str(it.get('price', '0')))
        total_price += p * q
        total_quantity += q
        it['total_price'] = float(p * q)  # keep per-item snapshot for the table

    return render(request, 'shop/cart.html', {
        'cart_items': cart,
        'total_price': float(total_price),
        'total_quantity': total_quantity,
    })

def checkout_view(request):
    cart = ensure_session_cart(request)

    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('cart')

    subtotal = Decimal('0.00')
    total_quantity = 0

    # ensure each item has total_price and compute totals
    for it in cart.values():
        q = int(it.get('quantity', 1))
        p = Decimal(str(it.get('price', '0')))
        it['total_price'] = float(p * q)
        subtotal += p * q
        total_quantity += q

    request.session['cart'] = cart
    return render(request, 'shop/checkout.html', {
        'cart_items': cart,
        'subtotal': float(subtotal),
        'shipping': 0.00,                 # demo
        'total_price': float(subtotal),   # subtotal + shipping in future
        'total_quantity': total_quantity,
    })


def process_checkout(request):
    """
    Convert the session cart into an Order + OrderItems, then clear the cart.
    - Uses Decimal for money (accurate).
    - Accepts cart entries keyed like "album_42" with values holding:
      {title, price(str), quantity(int), type, id, ...}
    """
    if request.method != "POST":
        return HttpResponse("Invalid request method.", status=405)

    cart = ensure_session_cart(request)
    if not cart:
        messages.error(request, "Your cart is empty. Add items before checking out.")
        return redirect("cart")

    # Create an order (demo: mark as paid)
    user = request.user if request.user.is_authenticated else None
    order = Order.objects.create(user=user, status="paid", total_amount=Decimal("0.00"))

    total = Decimal("0.00")
    for key, item in cart.items():
        # Try to get structured fields first
        item_type = item.get("type")
        item_id = item.get("id")
        title = item.get("title") or "Item"
        unit_price = Decimal(str(item.get("price", "0")))
        qty = int(item.get("quantity", 1))

        # Fallback: parse from key like "album_42"
        if not (item_type and item_id):
            if "_" in key:
                item_type, raw_id = key.split("_", 1)
                if raw_id.isdigit():
                    item_id = int(raw_id)

        if not (item_type and item_id):
            # Skip unknown rows gracefully
            continue

        OrderItem.objects.create(
            order=order,
            item_type=item_type,
            item_id=int(item_id),
            title=title,
            unit_price=unit_price,
            quantity=qty,
        )
        total += unit_price * qty

    order.total_amount = total
    order.save()

    # Clear cart & any legacy counters
    request.session["cart"] = {}
    if request.user.is_authenticated:
        CartItem.objects.filter(user=request.user).delete()
    for k in ("cart_count", "cart_total_price", "total_quantity"):
        request.session.pop(k, None)
    request.session.modified = True

    messages.success(request, f"Order #{order.pk} processed successfully (demo).")
    return redirect("success")



def success(request):
    return render(request, 'shop/success.html')

def remove_from_cart(request, item_type, item_id):
    # Retrieve the cart from session
    cart = ensure_session_cart(request)

    # Construct a unique key for this item using its type and ID
    item_key = f"{item_type}_{item_id}"

    # Check if the item exists in the cart and remove it
    if item_key in cart:
        del cart[item_key]
        messages.success(request, f"{item_type.capitalize()} removed from cart.")

    request.session['cart'] = cart
    request.session.modified = True

    payload = _cart_payload(request, f"{item_type.capitalize()} removed from cart.")
    if _wants_json(request):
        payload["removed_key"] = item_key
        return JsonResponse(payload)

    return redirect('cart')  # Redirect back to the cart page
  

def update_cart(request, album_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        album_id_str = str(album_id)
        album_key = f"album_{album_id}"

        cart = ensure_session_cart(request)
        item_key = album_key if album_key in cart else album_id_str
        if item_key in cart:
            cart[item_key]['quantity'] = quantity
            request.session['cart'] = cart
            request.session.modified = True
            save_session_cart_to_user(request)

    return redirect('cart')

# In your views.py, create a helper function to calculate total items in cart
def get_cart_total_quantity(request):
    cart = ensure_session_cart(request)
    total_quantity = sum(item['quantity'] for item in cart.values())
    return total_quantity

# Then pass this total quantity to your template context in views that render base.html

def update_cart_all(request):
    """
    Bulk-update cart quantities from inputs named like:
    - quantity_<item_type>_<item_id> (e.g., quantity_album_12)
    - qty-<item_type>-<item_id>     (e.g., qty-album-12)

    Rules:
    - non-numbers → treated as 0
    - qty <= 0    → remove item
    - totals are recomputed with Decimal (accurate money math)
    """
    if request.method != 'POST':
        return redirect('cart')

    cart = ensure_session_cart(request)
    if not isinstance(cart, dict):
        cart = {}

    updated = removed = 0

    # Accept both patterns
    parsed = []
    for key, raw in request.POST.items():
        if key.startswith('quantity_'):
            # quantity_album_1  -> ('album','1', value)
            try:
                _, item_type, item_id = key.split('_', 2)
                parsed.append((item_type, item_id, raw))
            except ValueError:
                pass
        elif key.startswith('qty-'):
            # qty-album-1 -> ('album','1', value)
            try:
                _, item_type, item_id = key.split('-', 2)
                parsed.append((item_type, item_id, raw))
            except ValueError:
                pass

    for item_type, item_id, raw in parsed:
        if not item_id.isdigit():
            continue
        try:
            qty = int(raw)
        except (TypeError, ValueError):
            qty = 0

        item_key = f"{item_type}_{item_id}"

        entry = cart.get(item_key)
        if not entry:
            continue

        if qty <= 0:
            del cart[item_key]
            removed += 1
            continue

        entry['quantity'] = qty
        # ensure total_price snapshot
        price = Decimal(str(entry.get('price', '0')))
        entry['total_price'] = float(price * qty)
        updated += 1

    request.session['cart'] = cart
    request.session.modified = True

    payload = _cart_payload(request, f"Cart updated ({updated} changed, {removed} removed).")
    if _wants_json(request):
        payload["updated"] = updated
        payload["removed"] = removed
        return JsonResponse(payload)

    messages.success(request, f"Cart updated ({updated} changed, {removed} removed).")
    return redirect('cart')

def track_catalog(request):
    q = (request.GET.get("q") or "").strip()
    exact = request.GET.get("exact")

    tracks = Track.objects.select_related(
        "album",
        "artist",
        "album__genre"
    ).order_by("album__title", "id")

    if q:
        if exact:
            tracks = tracks.filter(title__iexact=q)
        else:
            tracks = tracks.filter(
                Q(title__icontains=q) |
                Q(artist__name__icontains=q) |
                Q(album__title__icontains=q)
            )

    paginator = Paginator(tracks, 12)  # 12 tracks per page
    page_number = request.GET.get("page")
    tracks = paginator.get_page(page_number)

    return render(
        request,
        "shop/track_catalog.html",
        {
            "tracks": tracks,
            "q": q,
        }
    )

def landing_page(request):
    trending_albums = Album.objects.order_by('-sales')[:5]
    return render(request, 'shop/landing_page.html', {'trending_albums': trending_albums})

def merchandise_view(request):
    category = request.GET.get('category', 'all')  # default: 'all'
    q = (request.GET.get('q') or '').strip()       # allow search queries

    # Base queryset by category
    if category == 'tshirt':
        products = Tshirt.objects.all()
    elif category == 'vinyl':
        products = Vinyl.objects.all()
    elif category == 'poster':
        products = Poster.objects.all()
    else:
        # all merch types combined
        products = list(Tshirt.objects.all()) + list(Vinyl.objects.all()) + list(Poster.objects.all())

    # 🧠 Apply q= search if present
    if q:
        q_lower = q.lower()
        tshirts = Tshirt.objects.filter(
            Q(artist__name__icontains=q_lower) |
            Q(color__icontains=q_lower) |
            Q(size__icontains=q_lower)
        )
        vinyls = Vinyl.objects.filter(
            Q(artist__name__icontains=q_lower) |
            Q(edition__icontains=q_lower)
        )
        posters = Poster.objects.filter(
            Q(artist__name__icontains=q_lower) |
            Q(dimensions__icontains=q_lower)
        )

        # merge all into a single list
        products = list(tshirts) + list(vinyls) + list(posters)

    return render(request, 'shop/merchandise.html', {
        'products': products,
        'category': category,
        'q': q,
    })

def account(request):
    if not request.user.is_authenticated:
        messages.error(request, "You need to be logged in to view your account.")
        return redirect('login')

    user = request.user
    # You can add more user-related data here if needed
    return render(request, 'shop/account.html', {'user': user})
