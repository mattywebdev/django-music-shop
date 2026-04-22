from django import template
from shop.models import Tshirt, Vinyl, Poster, Favorite

register = template.Library()

@register.filter(name="add_class")
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.filter(name="instance_of")
def instance_of(value, class_name):
    """Usage: {{ obj|instance_of:'Tshirt' }}"""
    if value is None or not class_name:
        return False
    name = str(class_name).lower()
    # Match either the Python class name or Django model_name
    cls_name = value.__class__.__name__.lower()
    model_name = getattr(getattr(value, "_meta", None), "model_name", "").lower()
    return cls_name == name or model_name == name

@register.simple_tag
def is_favorite(user, item_type, item_id):
    """Return True if this item is in the user's favourites."""
    if not getattr(user, "is_authenticated", False):
        return False
    from shop.models import Favorite  # local import to avoid tag import cycles
    return Favorite.objects.filter(user=user, item_type=item_type, item_id=item_id).exists()


@register.filter
def file_url(f, default=""):
    """
    Safely return f.url or a default string if no file is attached.
    Usage: {{ obj.image|file_url:'/static/img/placeholder.png' }}
    """
    try:
        if f:
            return f.url
    except Exception:
        pass
    return default