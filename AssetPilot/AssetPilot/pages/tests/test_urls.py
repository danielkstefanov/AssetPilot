from django.test import TestCase
from django.urls import reverse, resolve
from pages.views import home_view, profile, import_trades, contact_us_view


class PagesURLTests(TestCase):

    def test_home_view_url_resolves(self):
        url = reverse("pages:home")
        self.assertEqual(resolve(url).func, home_view)

    def test_profile_url_resolves(self):
        url = reverse("pages:profile")
        self.assertEqual(resolve(url).func, profile)

    def test_import_trades_url_resolves(self):
        url = reverse("pages:import-trades")
        self.assertEqual(resolve(url).func, import_trades)

    def test_contact_us_view_url_resolves(self):
        url = reverse("pages:contact-us")
        self.assertEqual(resolve(url).func, contact_us_view)
