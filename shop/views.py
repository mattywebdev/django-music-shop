from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .serializers import ProductSerializer
from .models import (
    Album, Track, Tshirt, Vinyl, Poster, Ambient,
    Order, OrderItem, Genre, Artist, Favorite,
)
# If you keep the DRF view below, these are needed:
from rest_framework.decorators import api_view
from rest_framework.response import Response

def _safe_file_url(filefield, default=""):
    try:
        if filefield:
            return filefield.url
    except Exception:
        pass
    return default

def api_ping(request): return JsonResponse({"ok": True})


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
            messages.success(request, f"Account created for {username}! You can now log in.")
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
            return redirect('landing_page')
        else:
            messages.info(request, 'Username OR password is incorrect')
    return render(request, 'shop/login.html')


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

    cart = request.session.get('cart', {})
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

    # Recalculate totals
    total_qty = 0
    for it in cart.values():
        q = int(it.get('quantity', 1))
        p = Decimal(str(it.get('price', '0')))
        it['total_price'] = float(p * q)
        total_qty += q

    request.session['cart'] = cart
    request.session['total_quantity'] = total_qty
    request.session.modified = True

    messages.success(request, f"{item_title} added to your cart.")
    return redirect(request.META.get('HTTP_REFERER', 'landing_page'))


def cart_view(request):
    cart = request.session.get('cart', {})
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
    cart = request.session.get('cart', {})

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

    cart = request.session.get("cart", {})
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
    for k in ("cart_count", "cart_total_price", "total_quantity"):
        request.session.pop(k, None)
    request.session.modified = True

    messages.success(request, f"Order #{order.pk} processed successfully (demo).")
    return redirect("success")



def success(request):
    return render(request, 'shop/success.html')

def remove_from_cart(request, item_type, item_id):
    # Retrieve the cart from session
    cart = request.session.get('cart', {})

    # Construct a unique key for this item using its type and ID
    item_key = f"{item_type}_{item_id}"

    # Check if the item exists in the cart and remove it
    if item_key in cart:
        del cart[item_key]
        messages.success(request, f"{item_type.capitalize()} removed from cart.")

    # Recalculate total quantity after removal
    total_quantity = sum(item['quantity'] for item in cart.values())
    request.session['cart'] = cart
    request.session['total_quantity'] = total_quantity

    return redirect('cart')  # Redirect back to the cart page
  

def update_cart(request, album_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        album_id_str = str(album_id)

        cart = request.session.get('cart', {})
        if album_id_str in cart:
            cart[album_id_str]['quantity'] = quantity
            request.session['cart'] = cart

    return redirect('cart')

# In your views.py, create a helper function to calculate total items in cart
def get_cart_total_quantity(request):
    cart = request.session.get('cart', {})
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

    cart = request.session.get('cart', {})
    if not isinstance(cart, (dict, list)):
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

    # Recalc header totals
    total_qty = 0
    total_price = Decimal('0.00')
    for it in cart.values():
        q = int(it.get('quantity', 1))
        p = Decimal(str(it.get('price', '0')))
        total_qty += q
        total_price += p * q

    request.session['cart'] = cart
    request.session['total_quantity'] = total_qty
    request.session.modified = True

    messages.success(request, f"Cart updated ({updated} changed, {removed} removed).")
    return redirect('cart')

def track_catalog(request):
    q = (request.GET.get("q") or "").strip()
    exact = request.GET.get("exact")  # when present, show only exact title matches
    tracks = Track.objects.select_related("album", "artist", "album__genre")

    if q:
        if exact:
            tracks = tracks.filter(title__iexact=q)
        else:
            tracks = tracks.filter(
                Q(title__icontains=q) |
                Q(artist__name__icontains=q) |
                Q(album__title__icontains=q)
            )

    return render(request, "shop/track_catalog.html", {"tracks": tracks, "q": q})

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