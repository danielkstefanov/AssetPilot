from django.test import TestCase
from django.urls import reverse, resolve
from users.views import register_view, login_view, logout_view


class UsersURLTests(TestCase):

    def test_register_url_resolves(self):
        url = reverse("users:register")
        self.assertEqual(resolve(url).func, register_view)

    def test_login_url_resolves(self):
        url = reverse("users:login")
        self.assertEqual(resolve(url).func, login_view)

    def test_logout_url_resolves(self):
        url = reverse("users:logout")
        self.assertEqual(resolve(url).func, logout_view)
