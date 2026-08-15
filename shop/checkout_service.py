from decimal import Decimal

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.urls import reverse

from .models import Order, OrderItem
from .product_catalog import resolve_product, to_minor_units


class CheckoutError(Exception):
    """Raised when a cart cannot safely be converted into a checkout."""


def _cart_reference(key, item):
    item_type = item.get("type")
    item_id = item.get("id")
    if not (item_type and item_id) and "_" in key:
        item_type, raw_id = key.split("_", 1)
        item_id = raw_id if raw_id.isdigit() else None
    if not (item_type and item_id):
        raise CheckoutError("Your cart contains an invalid product reference.")
    return item_type, item_id


def resolve_cart(cart):
    if not isinstance(cart, dict) or not cart:
        raise CheckoutError("Your cart is empty.")

    lines = []
    for key, item in cart.items():
        if not isinstance(item, dict):
            raise CheckoutError("Your cart contains an invalid item.")
        item_type, item_id = _cart_reference(key, item)
        try:
            quantity = int(item.get("quantity", 1))
        except (TypeError, ValueError) as exc:
            raise CheckoutError("Your cart contains an invalid quantity.") from exc
        if quantity < 1:
            raise CheckoutError("Product quantities must be at least one.")

        try:
            product = resolve_product(item_type, item_id)
        except ValidationError as exc:
            raise CheckoutError(exc.messages[0]) from exc
        lines.append((product, quantity))
    return lines


@transaction.atomic
def create_pending_order(user, cart):
    lines = resolve_cart(cart)
    total = sum(
        (product.unit_price * quantity for product, quantity in lines),
        Decimal("0.00"),
    )
    order = Order.objects.create(
        user=user,
        status="pending",
        total_amount=total,
        checkout_email=(user.email or "").strip(),
    )
    OrderItem.objects.bulk_create([
        OrderItem(
            order=order,
            item_type=product.item_type,
            item_id=product.item_id,
            title=product.title,
            quantity=quantity,
            unit_price=product.unit_price,
        )
        for product, quantity in lines
    ])
    return order


def create_stripe_checkout_session(request, order):
    secret_key = settings.STRIPE_SECRET_KEY
    if not secret_key or not secret_key.startswith("sk_test_"):
        raise CheckoutError("Stripe test-mode checkout is not configured.")
    if settings.STRIPE_CURRENCY != "gbp":
        raise CheckoutError("Checkout is configured for GBP only.")

    order_id = str(order.pk)
    metadata = {"order_id": order_id, "user_id": str(order.user_id)}
    params = {
        "mode": "payment",
        "client_reference_id": order_id,
        "metadata": metadata,
        "payment_intent_data": {"metadata": metadata},
        "line_items": [
            {
                "price_data": {
                    "currency": "gbp",
                    "product_data": {"name": item.title},
                    "unit_amount": to_minor_units(item.unit_price),
                },
                "quantity": item.quantity,
            }
            for item in order.items.all()
        ],
        "name_collection": {
            "individual": {"enabled": True, "optional": False},
        },
        "success_url": (
            request.build_absolute_uri(reverse("success"))
            + "?session_id={CHECKOUT_SESSION_ID}"
        ),
        "cancel_url": request.build_absolute_uri(reverse("checkout_cancelled")),
    }

    email = (order.checkout_email or "").strip()
    if email:
        try:
            validate_email(email)
        except ValidationError:
            pass
        else:
            params["customer_email"] = email

    session = stripe.checkout.Session.create(
        **params,
        api_key=secret_key,
        idempotency_key=f"checkout-order-{order.pk}",
    )
    if not getattr(session, "id", None) or not getattr(session, "url", None):
        raise CheckoutError("Stripe returned an incomplete Checkout Session.")

    order.stripe_checkout_session_id = session.id
    order.save(update_fields=["stripe_checkout_session_id"])
    return session
