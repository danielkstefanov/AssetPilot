from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch
from markets.models import Trade, Strategy
from datetime import datetime
import json

User = get_user_model()


class TestMarketsHomeView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.com", password="danitester"
        )

        self.strategy = Strategy.objects.create(
            creator=self.user,
            title="Test Strategy",
            enter_position_explanation="Test Enter Position Explanation",
            trade_exit_explanation="Test Trade Exit Explanation",
        )

        self.trade = Trade.objects.create(
            user=self.user,
            ticker="AAPL",
            trade_type="BUY",
            amount=100,
            enter_price=150.00,
            enter_date=datetime.now(),
            is_open=True,
        )

    def test_markets_home_requires_login(self):
        response = self.client.get(reverse("markets:markets-home-view"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_markets_home_get_request(self):
        self.client.login(username="danitester", password="danitester")

        with patch("markets.views.get_ticker_price", return_value=160.00):
            response = self.client.get(reverse("markets:markets-home-view"))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "markets/markets.html")

            self.assertEqual(response.context["search_query"], "AAPL")
            self.assertTrue("open_trades_data" in response.context)
            self.assertTrue("strategies" in response.context)

            trades_data = response.context["open_trades_data"]
            self.assertEqual(len(trades_data), 1)
            trade_data = trades_data[0]
            self.assertEqual(trade_data["ticker"], "AAPL")
            self.assertEqual(trade_data["amount"], 100)
            self.assertEqual(float(trade_data["enter_price"]), 150.00)
            self.assertEqual(trade_data["profit_loss_percentage"], 6.67)

    def test_markets_home_post_request(self):
        self.client.login(username="danitester", password="danitester")

        with patch("markets.views.get_ticker_price", return_value=155.00):

            post_data = {
                "order_type": "BUY",
                "amount": 50,
                "strategy": "default",
            }

            response = self.client.post(
                reverse("markets:markets-home-view") + "?q=TSLA",
                data=post_data,
            )

            self.assertEqual(response.status_code, 200)

            response_data = response.json()
            self.assertEqual(response_data["status"], "success")
            self.assertEqual(response_data["trade"]["ticker"], "TSLA")
            self.assertEqual(response_data["trade"]["amount"], "50")
            self.assertEqual(float(response_data["trade"]["enter_price"]), 155.00)

            trade = Trade.objects.get(ticker="TSLA")
            self.assertEqual(trade.trade_type, "BUY")
            self.assertEqual(trade.amount, 50)
            self.assertEqual(float(trade.enter_price), 155.00)
            self.assertIsNone(trade.strategy)

    def test_markets_home_post_with_strategy(self):
        self.client.login(username="danitester", password="danitester")

        with patch("markets.views.get_ticker_price", return_value=155.00):

            post_data = {
                "order_type": "SELL",
                "amount": 75,
                "strategy": str(self.strategy.id),
            }

            response = self.client.post(
                reverse("markets:markets-home-view") + "?q=TSLA",
                data=post_data,
            )

            self.assertEqual(response.status_code, 200)

            trade = Trade.objects.get(amount=75)
            self.assertEqual(trade.strategy, self.strategy)

    def test_markets_home_with_search(self):
        self.client.login(username="danitester", password="danitester")

        response = self.client.get(reverse("markets:markets-home-view") + "?q=TSLA")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["search_query"], "TSLA")


class TestSearchStocksView(TestCase):
    def test_search_stocks_empty_query(self):
        response = self.client.get(reverse("markets:search-stocks"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_search_stocks_short_query(self):
        response = self.client.get(reverse("markets:search-stocks") + "?q=A")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_search_stocks_success(self):
        mock_api_response = {
            "result": [
                {
                    "description": "APPLE INC",
                    "displaySymbol": "AAPL",
                    "symbol": "AAPL",
                    "type": "Common Stock",
                },
                {
                    "description": "MICROSOFT CORP",
                    "displaySymbol": "MSFT",
                    "symbol": "MSFT",
                    "type": "Common Stock",
                },
                {
                    "description": "Some ETF",
                    "displaySymbol": "ETF",
                    "symbol": "ETF",
                    "type": "ETF",
                },
            ]
        }

        with patch(
            "markets.views.finnhub_client.symbol_lookup", return_value=mock_api_response
        ) as mock_lookup:

            response = self.client.get(reverse("markets:search-stocks") + "?q=APP")
            self.assertEqual(response.status_code, 200)
            results = response.json()
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["symbol"], "AAPL")
            self.assertEqual(results[0]["name"], "APPLE INC")
            self.assertEqual(results[1]["symbol"], "MSFT")
            self.assertEqual(results[1]["name"], "MICROSOFT CORP")
            mock_lookup.assert_called_once_with("APP")

    def test_search_stocks_api_error(self):
        with patch(
            "markets.views.finnhub_client.symbol_lookup",
            side_effect=Exception("API Error"),
        ) as mock_lookup:

            response = self.client.get(reverse("markets:search-stocks") + "?q=AAPL")
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {"error": "API Error"})

    def test_search_stocks_empty_results(self):
        mock_api_response = {"result": []}

        with patch(
            "markets.views.finnhub_client.symbol_lookup", return_value=mock_api_response
        ):

            response = self.client.get(
                reverse("markets:search-stocks") + "?q=NONEXISTENT"
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), [])


class TestCreateStrategyView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.com", password="danitester"
        )

        self.strategy_data = {
            "title": "Test Strategy",
            "enter_position_explanation": "Buy when RSI is below 30",
            "trade_exit_explanation": "Sell when RSI is above 70",
        }

    def test_create_strategy_requires_login(self):
        response = self.client.post(
            reverse("markets:create_strategy"),
            data=self.strategy_data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_create_strategy_success(self):
        self.client.login(username="danitester", password="danitester")

        response = self.client.post(
            reverse("markets:create_strategy"),
            data=json.dumps(self.strategy_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertTrue("id" in response_data)
        self.assertEqual(response_data["title"], self.strategy_data["title"])
        self.assertEqual(
            response_data["enter_position_explanation"],
            self.strategy_data["enter_position_explanation"],
        )
        self.assertEqual(
            response_data["trade_exit_explanation"],
            self.strategy_data["trade_exit_explanation"],
        )
        self.assertEqual(response_data["creator"], "danitester")

        strategy = Strategy.objects.get(id=response_data["id"])
        self.assertEqual(strategy.title, self.strategy_data["title"])
        self.assertEqual(strategy.creator, self.user)

    def test_create_strategy_invalid_data(self):
        self.client.login(username="danitester", password="danitester")

        invalid_data = {
            "enter_position_explanation": "Buy when RSI is below 30",
            "trade_exit_explanation": "Sell when RSI is above 70",
        }

        response = self.client.post(
            reverse("markets:create_strategy"),
            data=invalid_data,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Failed to create strategy"})


class TestGetStrategyDetailsView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.com", password="danitester"
        )

        self.strategy = Strategy.objects.create(
            creator=self.user,
            title="Test Strategy",
            enter_position_explanation="Buy when RSI is below 30",
            trade_exit_explanation="Sell when RSI is above 70",
        )

    def test_create_strategy_requires_login(self):
        response = self.client.get(
            reverse("markets:get_strategy_details", args=[self.strategy.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_get_strategy_details_success(self):
        self.client.login(username="danitester", password="danitester")

        response = self.client.get(
            reverse("markets:get_strategy_details", args=[self.strategy.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], self.strategy.title)
        self.assertEqual(
            response.json()["enter_position_explanation"],
            self.strategy.enter_position_explanation,
        )
        self.assertEqual(
            response.json()["trade_exit_explanation"],
            self.strategy.trade_exit_explanation,
        )

    def test_get_strategy_details_nonexistent_id(self):
        self.client.login(username="danitester", password="danitester")

        response = self.client.get(reverse("markets:get_strategy_details", args=[9999]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Strategy not found"})
