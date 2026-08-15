from .models import DigitalEntitlement


DIGITAL_PRODUCT_TYPES = {"album", "track"}


def ensure_order_entitlements(order):
    """Idempotently grant access from immutable items on a paid user order."""
    if order.status != "paid" or not order.user_id:
        return []

    entitlements = []
    for item in order.items.filter(item_type__in=DIGITAL_PRODUCT_TYPES):
        entitlement, _ = DigitalEntitlement.objects.get_or_create(
            order_item=item,
            defaults={
                "user_id": order.user_id,
                "order": order,
                "product_type": item.item_type,
                "product_id": item.item_id,
            },
        )
        entitlements.append(entitlement)
    return entitlements
