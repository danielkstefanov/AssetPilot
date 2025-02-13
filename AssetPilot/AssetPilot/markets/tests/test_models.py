from markets.models import Strategy, Trade

from django.test import TestCase
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from unittest.mock import patch
from django.db import IntegrityError


class StrategyModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.com", password="danitester"
        )

        self.strategy = Strategy.objects.create(
            title="Strategy",
            enter_position_explanation="enter explanation",
            trade_exit_explanation="exit explanation",
            creator=self.user,
        )

    def test_strategy_creation(self):
        self.assertEqual(self.strategy.title, "Strategy")
        self.assertEqual(self.strategy.enter_position_explanation, "enter explanation")
        self.assertEqual(self.strategy.trade_exit_explanation, "exit explanation")
        self.assertEqual(self.strategy.creator, self.user)

    def test_user_deletion_cascade(self):
        self.user.delete()
        self.assertEqual(Strategy.objects.count(), 0)


class TradeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.com", password="danitester"
        )

        self.strategy = Strategy.objects.create(
            title="Strategy",
            enter_position_explanation="enter explanation",
            trade_exit_explanation="exit explanation",
            creator=self.user,
        )

        self.trade_enter_date = datetime.now() - timedelta(days=1)

        self.trade = Trade.objects.create(
            user=self.user,
            strategy=self.strategy,
            ticker="AAPL",
            trade_type="BUY",
            amount=100,
            enter_price=100,
            enter_date=self.trade_enter_date,
            is_open=True,
        )

    def test_trade_creation(self):
        self.assertEqual(self.trade.user, self.user)
        self.assertEqual(self.trade.strategy, self.strategy)
        self.assertEqual(self.trade.ticker, "AAPL")
        self.assertEqual(self.trade.trade_type, "BUY")
        self.assertEqual(self.trade.amount, 100)
        self.assertEqual(self.trade.enter_price, 100)
        self.assertEqual(self.trade.enter_date, self.trade_enter_date)
        self.assertTrue(self.trade.is_open)

    def test_trade_close(self):
        with patch("markets.models.get_ticker_price", return_value=110):
            self.trade.close()
            self.assertFalse(self.trade.is_open)
            self.assertEqual(self.trade.close_price, 110)

    def test_trade_enter_price_must_be_greater_than_0(self):

        trade = Trade(
            user=self.user,
            strategy=self.strategy,
            ticker="AAPL",
            trade_type="BUY",
            amount=100,
            enter_price=-100,
            enter_date=self.trade_enter_date,
            is_open=True,
        )

        with self.assertRaises(IntegrityError):
            trade.save()

    def test_trade_amount_must_be_greater_than_0(self):

        trade = Trade(
            user=self.user,
            strategy=self.strategy,
            ticker="AAPL",
            trade_type="BUY",
            amount=-100,
            enter_price=100,
            enter_date=self.trade_enter_date,
            is_open=True,
        )

        with self.assertRaises(IntegrityError):
            trade.save()