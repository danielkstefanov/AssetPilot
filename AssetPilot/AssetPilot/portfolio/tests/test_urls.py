from django.test import TestCase
from django.urls import reverse, resolve
from portfolio.views import portfolio, portfolio_data, close_trade, trade_detail, get_trade_strategy


class PortfolioURLTests(TestCase):

    def test_portfolio_url_resolves(self):
        url = reverse("portfolio:portfolio")
        self.assertEqual(resolve(url).func, portfolio)

    def test_portfolio_data_url_resolves(self):
        url = reverse("portfolio:portfolio_data")
        self.assertEqual(resolve(url).func, portfolio_data)

    def test_close_trade_url_resolves(self):
        url = reverse("portfolio:close_trade", args=[1])
        self.assertEqual(resolve(url).func, close_trade)

    def test_trade_detail_url_resolves(self):
        url = reverse("portfolio:trade_detail", args=[1])
        self.assertEqual(resolve(url).func, trade_detail)

    def test_get_trade_strategy_url_resolves(self):
        url = reverse("portfolio:get_trade_strategy", args=[1])
        self.assertEqual(resolve(url).func, get_trade_strategy)
