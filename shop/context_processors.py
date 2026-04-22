from decimal import Decimal
from .models import Favorite
from hashlib import md5


def cart_total_price(request):
    cart_items = request.session.get('cart', {})
    total_price = sum(float(item['price']) * item['quantity'] for item in cart_items.values())
    return {'total_price': total_price}

def cart_summary(request):
    cart = request.session.get("cart", {}) or {}
    total_qty = 0
    total_price = Decimal("0.00")
    fav_count = 0

    if getattr(request.user, "is_authenticated", False):
        fav_count = Favorite.objects.filter(user=request.user).count()

    for item in cart.values():
        qty = int(item.get("quantity", 0) or 0)
        price = Decimal(str(item.get("price", "0") or "0"))
        total_qty += qty
        total_price += qty * price

    return {
        "cart_count": total_qty,
        "cart_total_price": total_price,
        "favorites_count": fav_count,
    }


def cart_badge(request):
    cart = request.session.get("cart", {})
    total_qty = 0
    total_price = Decimal("0")

    for it in cart.values():
        q = int(it.get("quantity", 1))
        p = Decimal(str(it.get("price", "0")))
        total_qty += q
        total_price += p * q

    # keep session mirrors if you like (optional)
    request.session["total_quantity"] = total_qty
    request.session["cart_total_price"] = f"{total_price:.2f}"

    return {
        "cart_count": total_qty,
        "cart_total_price": f"{total_price:.2f}",
    }

def _first_letter(user):
    name = (getattr(user, "first_name", "") or getattr(user, "username", "") or "").strip()
    return (name[:1] or "?").upper()

def _find_image_url(obj):
    """Try common attribute names on obj and return .url if present."""
    if not obj:
        return None
    for name in ("avatar", "photo", "image", "picture", "profile_image"):
        f = getattr(obj, name, None)
        try:
            if f and getattr(f, "url", None):
                return f.url
        except Exception:
            pass
    return None

def user_avatar(request):
    """Provide avatar_url and avatar_initial for templates."""
    u = request.user
    avatar_url = None
    avatar_initial = None
    avatar_bg = None  # nice, stable color for initial

    if u.is_authenticated:
        # 1) try directly on the user
        avatar_url = _find_image_url(u)

        # 2) try a related 'profile'
        if not avatar_url:
            profile = getattr(u, "profile", None)
            avatar_url = _find_image_url(profile)

        # initial + color
        avatar_initial = _first_letter(u)
        # stable pastel color from username/email hash
        key = (getattr(u, "username", "") or getattr(u, "email", "")).encode("utf-8")
        h = md5(key).hexdigest()
        hue = int(h[:2], 16) % 360
        avatar_bg = f"hsl({hue} 80% 35% / .85)"

    return {
        "avatar_url": avatar_url,
        "avatar_initial": avatar_initial,
        "avatar_bg": avatar_bg,
    }