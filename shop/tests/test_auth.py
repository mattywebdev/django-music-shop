# shop/tests/test_auth.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.contrib import messages
from django.http import HttpResponse

class AuthViewsTests(TestCase):
    def test_register_creates_user_and_redirects(self):
        r = self.client.post(reverse("register"), {
            "username": "newbie",
            "password1": "UltraSafePass123",
            "password2": "UltraSafePass123",
        }, follow=True)
        self.assertTrue(User.objects.filter(username="newbie").exists())
        # lands on login page after successful register
        self.assertEqual(r.resolver_match.url_name, "login")

    def test_login_invalid_shows_message_and_stays(self):
        r = self.client.post(reverse("login"), {
            "username": "ghost",
            "password": "nope",
        }, follow=True)
        self.assertContains(r, "Username OR password is incorrect")
        self.assertEqual(r.resolver_match.url_name, "login")

    def test_login_ignores_non_auth_messages(self):
        session = self.client.session
        session.save()
        request = RequestFactory().get(reverse("login"))
        SessionMiddleware(lambda req: None).process_request(request)
        request.session = session
        request._messages = FallbackStorage(request)
        messages.success(request, "Album removed from cart.")
        response = HttpResponse()
        request._messages.update(response=response)
        self.client.cookies.update(response.cookies)

        r = self.client.get(reverse("login"))

        self.assertNotContains(r, "Album removed from cart.")
        r = self.client.get(reverse("login"))
        self.assertNotContains(r, "Album removed from cart.")

    def test_login_and_logout_flow(self):
        User.objects.create_user(username="accu", password="pw12345")
        r = self.client.post(reverse("login"), {
            "username": "accu",
            "password": "pw12345",
        }, follow=True)
        self.assertEqual(r.resolver_match.url_name, "landing_page")
        # now logout
        r2 = self.client.get(reverse("logout"), follow=True)
        self.assertEqual(r2.resolver_match.url_name, "login")
