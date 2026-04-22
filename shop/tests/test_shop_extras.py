from django.test import TestCase
from django.contrib.auth.models import User
from shop.templatetags.shop_extras import is_favorite
from shop.models import Favorite

class ShopExtrasTests(TestCase):
    def test_is_favorite_tag(self):
        u = User.objects.create_user("tagu", password="p")
        self.assertFalse(is_favorite(u, "album", 1))
        Favorite.objects.create(user=u, item_type="album", item_id=1, title="T")
        self.assertTrue(is_favorite(u, "album", 1))
