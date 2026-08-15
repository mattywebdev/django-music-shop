from collections.abc import Mapping

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Order, StripeEvent
from .product_catalog import to_minor_units


PAYMENT_SUCCESS_EVENTS = {
    "checkout.session.completed",
    "checkout.session.async_payment_succeeded",
}


class WebhookValidationError(Exception):
    """Raised when a verified Stripe event contradicts the local order."""


def _field(obj, name, default=None):
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _metadata_value(session, name):
    metadata = _field(session, "metadata", {}) or {}
    return _field(metadata, name)


def _payment_intent_id(session):
    payment_intent = _field(session, "payment_intent")
    if isinstance(payment_intent, str):
        return payment_intent
    return _field(payment_intent, "id", "") or ""


def _validated_order(session):
    session_id = _field(session, "id")
    if not session_id:
        raise WebhookValidationError("Checkout Session ID is missing.")

    try:
        order = Order.objects.select_for_update().get(
            stripe_checkout_session_id=session_id
        )
    except Order.DoesNotExist as exc:
        raise WebhookValidationError("Checkout Session does not match an order.") from exc

    expected_order_id = str(order.pk)
    if str(_field(session, "client_reference_id", "")) != expected_order_id:
        raise WebhookValidationError("Checkout client reference does not match.")
    if str(_metadata_value(session, "order_id") or "") != expected_order_id:
        raise WebhookValidationError("Checkout metadata does not match.")
    if str(_metadata_value(session, "user_id") or "") != str(order.user_id):
        raise WebhookValidationError("Checkout user metadata does not match.")
    if _field(session, "mode") != "payment":
        raise WebhookValidationError("Checkout Session mode is invalid.")
    if (
        settings.STRIPE_CURRENCY != "gbp"
        or (_field(session, "currency") or "").lower() != "gbp"
    ):
        raise WebhookValidationError("Checkout currency does not match.")

    amount_total = _field(session, "amount_total")
    if isinstance(amount_total, bool) or not isinstance(amount_total, int):
        raise WebhookValidationError("Checkout total is invalid.")
    if amount_total != to_minor_units(order.total_amount):
        raise WebhookValidationError("Checkout total does not match the order.")

    payment_intent_id = _payment_intent_id(session)
    if not payment_intent_id:
        raise WebhookValidationError("PaymentIntent ID is missing.")
    if (
        order.stripe_payment_intent_id
        and order.stripe_payment_intent_id != payment_intent_id
    ):
        raise WebhookValidationError("PaymentIntent does not match the order.")
    return order, payment_intent_id


def process_checkout_payment_event(event):
    event_id = _field(event, "id")
    event_type = _field(event, "type")
    if not event_id or not event_type:
        raise WebhookValidationError("Stripe event identity is missing.")
    if event_type not in PAYMENT_SUCCESS_EVENTS:
        return "ignored"

    session = _field(_field(event, "data", {}), "object")
    if session is None:
        raise WebhookValidationError("Checkout Session data is missing.")

    # A completed Session can still be processing for delayed payment methods.
    # Stripe later sends checkout.session.async_payment_succeeded when it is paid.
    if _field(session, "payment_status") != "paid":
        if event_type == "checkout.session.completed":
            return "awaiting_payment"
        raise WebhookValidationError("Checkout Session is not paid.")

    try:
        with transaction.atomic():
            if StripeEvent.objects.filter(event_id=event_id).exists():
                return "duplicate"

            order, payment_intent_id = _validated_order(session)
            if order.status == "pending":
                transitioned = Order.objects.filter(
                    pk=order.pk,
                    status="pending",
                ).update(
                    status="paid",
                    paid_at=timezone.now(),
                    stripe_payment_intent_id=payment_intent_id,
                )
                if not transitioned:
                    order.refresh_from_db()
                    if order.status != "paid":
                        raise WebhookValidationError(
                            "Only pending orders can transition to paid."
                        )
                    if order.stripe_payment_intent_id != payment_intent_id:
                        raise WebhookValidationError(
                            "PaymentIntent does not match the order."
                        )
            elif order.status == "paid":
                if not order.stripe_payment_intent_id:
                    order.stripe_payment_intent_id = payment_intent_id
                    order.save(update_fields=["stripe_payment_intent_id"])
            else:
                raise WebhookValidationError(
                    "Only pending orders can transition to paid."
                )

            StripeEvent.objects.create(
                event_id=event_id,
                event_type=event_type,
                order=order,
            )
            return "processed"
    except IntegrityError:
        # A concurrent delivery may win the unique event-ID race.
        if StripeEvent.objects.filter(event_id=event_id).exists():
            return "duplicate"
        raise
