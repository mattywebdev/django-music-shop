from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.exceptions import ValidationError

from .models import Album, Ambient, Poster, Track, Tshirt, Vinyl


GBP_QUANTUM = Decimal("0.01")


class ProductResolutionError(ValidationError):
    """Raised when a cart reference cannot produce a purchasable product."""


@dataclass(frozen=True)
class ResolvedProduct:
    item_type: str
    item_id: int
    title: str
    unit_price: Decimal


def normalise_price(value) -> Decimal:
    try:
        price = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ProductResolutionError("Product has an invalid price.") from exc

    if not price.is_finite() or price <= 0:
        raise ProductResolutionError("Product price must be greater than zero.")
    if price != price.quantize(GBP_QUANTUM):
        raise ProductResolutionError("GBP prices must have no more than two decimal places.")
    return price.quantize(GBP_QUANTUM)


def to_minor_units(amount: Decimal) -> int:
    """Convert an exact GBP Decimal amount to pence without using floats."""
    amount = normalise_price(amount)
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def resolve_product(item_type: str, item_id: int) -> ResolvedProduct:
    item_type = (item_type or "").lower()
    try:
        item_id = int(item_id)
    except (TypeError, ValueError) as exc:
        raise ProductResolutionError("Product ID is invalid.") from exc
    if item_id <= 0:
        raise ProductResolutionError("Product ID is invalid.")

    model_map = {
        "album": Album,
        "track": Track,
        "ambient": Ambient,
        "tshirt": Tshirt,
        "vinyl": Vinyl,
        "poster": Poster,
    }
    model = model_map.get(item_type)
    if model is None:
        raise ProductResolutionError("Unsupported product type.")

    try:
        product = model.objects.select_related("artist").get(pk=item_id)
    except model.DoesNotExist as exc:
        raise ProductResolutionError("Product is no longer available.") from exc

    if item_type == "album":
        title = product.title
        price = product.price
    elif item_type == "track":
        title = product.title
        price = product.get_price()
    elif item_type == "ambient":
        title = product.name
        price = product.price
    else:
        title = str(product)
        price = product.price

    return ResolvedProduct(
        item_type=item_type,
        item_id=item_id,
        title=title,
        unit_price=normalise_price(price),
    )
