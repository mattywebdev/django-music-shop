from django import forms
from django.test import TestCase, RequestFactory, SimpleTestCase
from django.contrib.auth.models import AnonymousUser
from shop.templatetags.custom_filters import add_class
from shop.templatetags.shop_extras import is_favorite

class DummyForm(forms.Form):
    name = forms.CharField()

class CustomFiltersMoreTests(SimpleTestCase):
    def test_add_class_injects_css_class(self):
        f = DummyForm()
        html = add_class(f["name"], "form-control")
        self.assertIn('class="form-control"', html)

class ShopExtrasAnonTests(TestCase):
    def test_is_favorite_false_for_anonymous(self):
        req = RequestFactory().get("/")
        req.user = AnonymousUser()
        self.assertFalse(is_favorite(req.user, "album", 1))
