from django import template
from shop.models import Favorite

register = template.Library()

@register.simple_tag
def is_favorite(user, item_type, item_id):
    """
    Return True if this item is in the user's favourites.
    Safe for anonymous users.
    """
    if not getattr(user, "is_authenticated", False):
        return False
    return Favorite.objects.filter(
        user=user, item_type=item_type, item_id=item_id
    ).exists()