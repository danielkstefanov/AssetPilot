from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch
from markets.models import Trade, Strategy
from decimal import Decimal
from datetime import datetime
import uuid

User = get_user_model()

TRADES_DATA = {
    "buy_trade": {
        "ticker": "AAPL",
        "trade_type": "BUY",
        "amount": 100,
        "enter_price": Decimal("150.00"),
        "is_open": True,
    },
    "sell_trade": {
        "ticker": "TSLA",
        "trade_type": "SELL",
        "amount": 50,
        "enter_price": Decimal("250.00"),
        "is_open": True,
    },
    "closed_trade": {
        "ticker": "MSFT",
        "trade_type": "BUY",
        "amount": 75,
        "enter_price": Decimal("300.00"),
        "close_price": Decimal("330.00"),
        "is_open": False,
    },
}


def get_price(ticker):
    prices = {
        "AAPL": 165.00,
        "TSLA": 225.00,
    }
    return prices.get(ticker, 0)


class TestPortfolioView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.bg", password="danitester"
        )

        default_date = datetime.now()

        self.buy_trade = Trade.objects.create(
            user=self.user, enter_date=default_date, **TRADES_DATA["buy_trade"]
        )

        self.sell_trade = Trade.objects.create(
            user=self.user, enter_date=default_date, **TRADES_DATA["sell_trade"]
        )

        self.closed_trade = Trade.objects.create(
            user=self.user,
            enter_date=default_date,
            close_date=default_date,
            **TRADES_DATA["closed_trade"]
        )

    def test_portfolio_requires_login(self):
        response = self.client.get(reverse("portfolio:portfolio"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_portfolio_view_with_trades(self):
        self.client.login(username="danitester", password="danitester")

        with patch("portfolio.views.get_ticker_price", side_effect=get_price):
            response = self.client.get(reverse("portfolio:portfolio"))

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "portfolio/portfolio.html")

            trades_data = response.context["open_trades_data"]
            self.assertEqual(len(trades_data), 2)

            buy_trade_data = next(t for t in trades_data if t["ticker"] == "AAPL")
            self.assertEqual(buy_trade_data["ticker"], "AAPL")
            self.assertEqual(float(buy_trade_data["enter_price"]), 150.00)
            self.assertEqual(buy_trade_data["current_price"], 165.00)
            self.assertEqual(buy_trade_data["profit_loss_percentage"], 10.00)

            sell_trade_data = next(t for t in trades_data if t["ticker"] == "TSLA")
            self.assertEqual(sell_trade_data["ticker"], "TSLA")
            self.assertEqual(float(sell_trade_data["enter_price"]), 250.00)
            self.assertEqual(sell_trade_data["current_price"], 225.00)
            self.assertEqual(sell_trade_data["profit_loss_percentage"], 10.00)

    def test_portfolio_view_no_trades(self):
        User.objects.create_user(
            username="danitester2", email="danitester2@abv.com", password="danitester2"
        )

        self.client.login(username="danitester2", password="danitester2")

        response = self.client.get(reverse("portfolio:portfolio"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "portfolio/portfolio.html")
        self.assertEqual(len(response.context["open_trades_data"]), 0)

    def test_portfolio_view_other_user_trades(self):
        other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )

        Trade.objects.create(
            user=other_user,
            ticker="GOOGL",
            trade_type="BUY",
            amount=25,
            enter_price=Decimal("2500.00"),
            enter_date=datetime.now(),
            is_open=True,
        )

        self.client.login(username="danitester", password="danitester")

        with patch("portfolio.views.get_ticker_price", return_value=2600.00):
            response = self.client.get(reverse("portfolio:portfolio"))

            trades_data = response.context["open_trades_data"]
            tickers = [trade["ticker"] for trade in trades_data]

            self.assertNotIn("GOOGL", tickers)
            self.assertIn("AAPL", tickers)
            self.assertIn("TSLA", tickers)


class TestPortfolioDataView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.bg", password="danitester"
        )

        self.buy_trade = Trade.objects.create(
            user=self.user, enter_date=datetime.now(), **TRADES_DATA["buy_trade"]
        )

        self.sell_trade = Trade.objects.create(
            user=self.user, enter_date=datetime.now(), **TRADES_DATA["sell_trade"]
        )

    def test_portfolio_data_requires_login(self):
        response = self.client.get(reverse("portfolio:portfolio_data"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_portfolio_data_calculations(self):
        self.client.login(username="danitester", password="danitester")

        with patch("portfolio.views.get_ticker_price", side_effect=get_price):
            with patch(
                "portfolio.views.create_suggestions", return_value=["Test suggestion"]
            ):
                response = self.client.get(reverse("portfolio:portfolio_data"))

                self.assertEqual(response.status_code, 200)
                data = response.json()

                aapl_value = 100 * 150.00
                new_aapl_value = 100 * 165.00
                tsla_value = 50 * 250.00
                new_tsla_value = 50 * 225.00

                original_size = aapl_value + tsla_value
                total_value = (
                    new_aapl_value + tsla_value - (new_tsla_value - tsla_value)
                )

                self.assertAlmostEqual(data["portfolio_value"], total_value, places=2)

                allocation = data["allocation"]
                self.assertEqual(len(allocation), 2)

                aapl_alloc = next(a for a in allocation if a["symbol"] == "AAPL")
                self.assertAlmostEqual(aapl_alloc["value"], new_aapl_value, places=2)
                self.assertAlmostEqual(
                    aapl_alloc["percentage"],
                    (new_aapl_value / total_value * 100),
                    places=2,
                )

                expected_return_value = total_value - original_size
                expected_return_percentage = (
                    expected_return_value / original_size
                ) * 100

                self.assertAlmostEqual(
                    data["portfolio_return_value"], expected_return_value, places=2
                )
                self.assertAlmostEqual(
                    data["portfolio_return_percentage"],
                    expected_return_percentage,
                    places=2,
                )

                self.assertEqual(data["suggestions"], ["Test suggestion"])

    def test_portfolio_data_no_trades(self):
        User.objects.create_user(
            username="danitester2", email="danitester2@abv.bg", password="danitester2"
        )

        self.client.login(username="danitester2", password="danitester2")

        with patch("portfolio.views.create_suggestions", return_value=[]):
            response = self.client.get(reverse("portfolio:portfolio_data"))

            self.assertEqual(response.status_code, 200)
            data = response.json()

            self.assertEqual(data["portfolio_value"], 0)
            self.assertEqual(data["portfolio_return_value"], 0)
            self.assertEqual(data["portfolio_return_percentage"], 0)
            self.assertEqual(len(data["allocation"]), 0)


class TestCloseTradeView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.bg", password="danitester"
        )

        self.open_trade = Trade.objects.create(
            user=self.user, enter_date=datetime.now(), **TRADES_DATA["buy_trade"]
        )

    def test_close_trade_requires_login(self):
        response = self.client.post(
            reverse("portfolio:close_trade", kwargs={"trade_id": self.open_trade.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_close_trade_requires_post(self):
        self.client.login(username="danitester", password="danitester")

        response = self.client.get(
            reverse("portfolio:close_trade", kwargs={"trade_id": self.open_trade.id})
        )
        self.assertEqual(response.status_code, 405)

    def test_close_trade_success(self):
        self.client.login(username="danitester", password="danitester")

        with patch("markets.models.Trade.close"):
            response = self.client.post(
                reverse(
                    "portfolio:close_trade", kwargs={"trade_id": self.open_trade.id}
                )
            )

            self.assertEqual(response.status_code, 200)
            response_data = response.json()
            self.assertEqual(response_data["status"], "success")
            self.assertEqual(response_data["message"], "Trade closed successfully")

    def test_close_trade_not_found(self):
        self.client.login(username="danitester", password="danitester")

        non_existent_id = 666
        response = self.client.post(
            reverse("portfolio:close_trade", kwargs={"trade_id": non_existent_id})
        )

        self.assertEqual(response.status_code, 500)
        response_data = response.json()
        self.assertEqual(response_data["status"], "error")

    def test_close_other_user_trade(self):
        User.objects.create_user(
            username="danitester2", email="danitester2@abv.bg", password="danitester2"
        )

        self.client.login(username="danitester2", password="danitester2")

        response = self.client.post(
            reverse("portfolio:close_trade", kwargs={"trade_id": self.open_trade.id})
        )

        self.assertEqual(response.status_code, 500)
        response_data = response.json()
        self.assertEqual(response_data["status"], "error")


class TestTradeDetailView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.bg", password="danitester"
        )

        default_date = datetime.now()

        self.buy_trade = Trade.objects.create(
            user=self.user, enter_date=default_date, **TRADES_DATA["buy_trade"]
        )

        self.sell_trade = Trade.objects.create(
            user=self.user, enter_date=default_date, **TRADES_DATA["sell_trade"]
        )

        self.closed_trade = Trade.objects.create(
            user=self.user,
            enter_date=default_date,
            close_date=default_date,
            **TRADES_DATA["closed_trade"]
        )

    def test_trade_detail_requires_login(self):
        response = self.client.get(
            reverse("portfolio:trade_detail", kwargs={"trade_id": self.buy_trade.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_trade_detail_open_buy_trade(self):
        self.client.login(username="danitester", password="danitester")

        current_price = 165.00

        with patch("portfolio.views.get_ticker_price", return_value=current_price):
            with patch(
                "portfolio.views.ai_analysis_for_trade", return_value="AI Analysis"
            ):
                response = self.client.get(
                    reverse(
                        "portfolio:trade_detail",
                        kwargs={"trade_id": self.buy_trade.id},
                    )
                )

                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "portfolio/trade_detail.html")

                context = response.context
                self.assertEqual(context["trade"], self.buy_trade)
                self.assertEqual(context["current_price"], 165.00)
                self.assertEqual(context["profit_loss"], 10)
                self.assertEqual(context["profit_loss_amount"], 1500.00)
                self.assertEqual(context["ai_analysis"], "AI Analysis")

    def test_trade_detail_open_sell_trade(self):
        self.client.login(username="danitester", password="danitester")

        current_price = 200.00

        with patch("portfolio.views.get_ticker_price", return_value=current_price):
            with patch(
                "portfolio.views.ai_analysis_for_trade", return_value="AI Analysis"
            ):
                response = self.client.get(
                    reverse(
                        "portfolio:trade_detail",
                        kwargs={"trade_id": self.sell_trade.id},
                    )
                )

                self.assertEqual(response.status_code, 200)
                context = response.context
                self.assertEqual(context["profit_loss"], 20.00)
                self.assertEqual(context["profit_loss_amount"], 50 * 50)

    def test_trade_detail_closed_trade(self):
        self.client.login(username="danitester", password="danitester")

        with patch("portfolio.views.ai_analysis_for_trade", return_value="AI Analysis"):
            response = self.client.get(
                reverse(
                    "portfolio:trade_detail", kwargs={"trade_id": self.closed_trade.id}
                )
            )

            self.assertEqual(response.status_code, 200)
            context = response.context
            self.assertEqual(context["current_price"], 330.00)
            self.assertEqual(context["profit_loss"], 10.00)
            self.assertEqual(context["profit_loss_amount"], 75 * 30)

    def test_trade_detail_not_found(self):
        self.client.login(username="danitester", password="danitester")

        response = self.client.get(
            reverse("portfolio:trade_detail", kwargs={"trade_id": 666})
        )

        self.assertEqual(response.status_code, 404)

    def test_trade_detail_other_user_trade(self):
        User.objects.create_user(
            username="danitester2", email="danitester2@abv.bg", password="danitester2"
        )
        self.client.login(username="danitester2", password="danitester2")

        response = self.client.get(
            reverse("portfolio:trade_detail", kwargs={"trade_id": self.buy_trade.id})
        )

        self.assertEqual(response.status_code, 404)



class TestGetTradeStrategyView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester",
            email="danitester@abv.bg",
            password="danitester"
        )
        
        self.strategy = Strategy.objects.create(
            creator=self.user,
            title="Test Strategy",
            enter_position_explanation="Buy when RSI is low",
            trade_exit_explanation="Sell when RSI is high"
        )
        
        self.trade_with_strategy = Trade.objects.create(
            user=self.user,
            strategy=self.strategy,
            enter_date=datetime.now(),
            **TRADES_DATA["buy_trade"]
        )
        
        self.trade_without_strategy = Trade.objects.create(
            user=self.user,
            strategy=None,
            enter_date=datetime.now(),
            **TRADES_DATA["sell_trade"]
        )

    def test_get_trade_strategy_requires_login(self):
        response = self.client.get(
            reverse('portfolio:get_trade_strategy', 
                   kwargs={'trade_id': self.trade_with_strategy.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_get_trade_strategy_with_strategy(self):
        self.client.login(username="danitester", password="danitester")
        
        response = self.client.get(
            reverse('portfolio:get_trade_strategy', 
                   kwargs={'trade_id': self.trade_with_strategy.id})
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        self.assertIsNotNone(data['strategy'])
        
        strategy = data['strategy']
        self.assertEqual(strategy['title'], self.strategy.title)
        self.assertEqual(
            strategy['enter_position_explanation'], 
            self.strategy.enter_position_explanation
        )
        self.assertEqual(
            strategy['trade_exit_explanation'], 
            self.strategy.trade_exit_explanation
        )

    def test_get_trade_strategy_without_strategy(self):
        self.client.login(username="danitester", password="danitester")
        
        response = self.client.get(
            reverse('portfolio:get_trade_strategy', 
                   kwargs={'trade_id': self.trade_without_strategy.id})
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        self.assertIsNone(data['strategy'])

    def test_get_trade_strategy_not_found(self):
        self.client.login(username="danitester", password="danitester")
        
        response = self.client.get(
            reverse('portfolio:get_trade_strategy', 
                   kwargs={'trade_id': 666})
        )
        
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data['status'], 'error')