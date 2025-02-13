from django.test import TestCase
from django.urls import reverse, resolve
from markets.views import (
    markets_home_view,
    search_stocks,
    create_strategy,
    get_strategy_details,
)


class MarketsURLTests(TestCase):

    def test_markets_home_view_url_resolves(self):
        url = reverse("markets:markets-home-view")
        self.assertEqual(resolve(url).func, markets_home_view)

    def test_search_stocks_url_resolves(self):
        url = reverse("markets:search-stocks")
        self.assertEqual(resolve(url).func, search_stocks)

    def test_create_strategy_url_resolves(self):
        url = reverse("markets:create_strategy")
        self.assertEqual(resolve(url).func, create_strategy)

    def test_get_strategy_details_url_resolves(self):
        url = reverse("markets:get_strategy_details", args=[1])
        self.assertEqual(resolve(url).func, get_strategy_details)
