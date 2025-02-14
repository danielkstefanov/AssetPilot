from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from markets.models import Trade, Strategy
from decimal import Decimal
from datetime import datetime
from django.core.files.uploadedfile import SimpleUploadedFile
import csv
from io import StringIO

User = get_user_model()

TRADE_DATA = {
    "open_trade": {
        "ticker": "AAPL",
        "trade_type": "BUY",
        "amount": 100,
        "enter_price": Decimal("150.00"),
        "is_open": True,
    },
    "closed_trade": {
        "ticker": "TSLA",
        "trade_type": "SELL",
        "amount": 50,
        "enter_price": Decimal("200.00"),
        "close_price": Decimal("180.00"),
        "is_open": False,
    },
}


class TestHomeView(TestCase):
    def test_home_view_get(self):
        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")

    def test_home_view_accessible_when_not_logged_in(self):
        response = self.client.get(reverse("pages:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")

    def test_home_view_accessible_when_logged_in(self):
        User.objects.create_user(
            username="danitester", email="danitester@abv.bg", password="danitester"
        )
        self.client.login(username="danitester", password="danitester")

        response = self.client.get(reverse("pages:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")


class TestProfileView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.bg", password="danitester"
        )

        self.strategy = Strategy.objects.create(
            creator=self.user,
            title="Test Strategy",
            enter_position_explanation="Buy when RSI is low",
            trade_exit_explanation="Sell when RSI is high",
        )

        self.open_trade = Trade.objects.create(
            user=self.user, enter_date=datetime.now(), **TRADE_DATA["open_trade"]
        )

        self.closed_trade = Trade.objects.create(
            user=self.user,
            enter_date=datetime.now(),
            close_date=datetime.now(),
            **TRADE_DATA["closed_trade"],
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse("pages:profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_profile_view_with_data(self):
        self.client.login(username="danitester", password="danitester")

        current_price = 165.00

        with patch("pages.views.get_ticker_price", return_value=current_price):
            response = self.client.get(reverse("pages:profile"))

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "pages/profile.html")

            context = response.context
            self.assertEqual(context["user"], self.user)

            open_trades = context["open_trades_data"]
            self.assertEqual(len(open_trades), 1)
            open_trade = open_trades[0]
            self.assertEqual(open_trade["ticker"], "AAPL")
            self.assertEqual(float(open_trade["enter_price"]), 150.00)
            self.assertEqual(open_trade["current_price"], 165.00)
            self.assertEqual(open_trade["profit_loss_percentage"], 10.00)

            closed_trades = context["closed_trades_data"]
            self.assertEqual(len(closed_trades), 1)
            closed_trade = closed_trades[0]
            self.assertEqual(closed_trade["ticker"], "TSLA")
            self.assertEqual(float(closed_trade["enter_price"]), 200.00)
            self.assertEqual(float(closed_trade["close_price"]), 180.00)
            self.assertEqual(closed_trade["profit_loss_percentage"], -10.00)

            strategies = context["strategies"]
            self.assertEqual(len(strategies), 1)
            self.assertEqual(strategies[0], self.strategy)

    def test_profile_view_no_data(self):
        User.objects.create_user(
            username="danitester2", email="danitester2@abv.bg", password="danitester2"
        )

        self.client.login(username="danitester2", password="danitester2")

        with patch("pages.views.get_ticker_price", return_value=0):
            response = self.client.get(reverse("pages:profile"))

            self.assertEqual(response.status_code, 200)
            context = response.context
            self.assertEqual(len(context["open_trades_data"]), 0)
            self.assertEqual(len(context["closed_trades_data"]), 0)
            self.assertEqual(len(context["strategies"]), 0)

    def test_profile_view_price_error(self):
        self.client.login(username="danitester", password="danitester")

        with patch("pages.views.get_ticker_price", side_effect=Exception("API Error")):
            response = self.client.get(reverse("pages:profile"))

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["open_trades_data"]), 1)
            self.assertEqual(len(response.context["closed_trades_data"]), 1)


class TestContactUsView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.bg", password="danitester"
        )

        self.valid_data = {"subject": "Test Subject", "message": "Test message content"}

    def test_contact_us_requires_login(self):
        response = self.client.get(reverse("pages:contact-us"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_contact_us_get(self):
        self.client.login(username="danitester", password="danitester")

        response = self.client.get(reverse("pages:contact-us"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/contact-us.html")

    def test_contact_us_post_success(self):
        self.client.login(username="danitester", password="danitester")

        with patch("pages.views.mailjet") as mock_mailjet:
            mock_send = MagicMock()
            mock_mailjet.send = mock_send

            response = self.client.post(
                reverse("pages:contact-us"), data=self.valid_data
            )

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "pages/contact-us.html")

            mock_send.create.assert_called_once()

            call_args = mock_send.create.call_args[1]
            email_data = call_args["data"]["Messages"][0]

            self.assertEqual(email_data["From"]["Email"], "danitester@abv.bg")
            self.assertEqual(email_data["From"]["Name"], "Asset Pilot")
            self.assertEqual(email_data["To"][0]["Email"], "fishingmaniabg@abv.bg")
            self.assertEqual(email_data["To"][0]["Name"], "Support Team")
            self.assertEqual(email_data["Subject"], "Test Subject")
            self.assertEqual(
                email_data["TextPart"],
                f"Message from danitester@abv.bg:\n\nTest message content",
            )

    def test_contact_us_post_missing_subject(self):
        self.client.login(username="danitester", password="danitester")

        with patch("pages.views.mailjet") as mock_mailjet:
            mock_send = MagicMock()
            mock_mailjet.send = mock_send

            response = self.client.post(
                reverse("pages:contact-us"), data={"message": "Test message"}
            )

            self.assertEqual(response.status_code, 200)
            mock_send.create.assert_not_called()

    def test_contact_us_post_missing_message(self):
        self.client.login(username="danitester", password="danitester")

        with patch("pages.views.mailjet") as mock_mailjet:
            mock_send = MagicMock()
            mock_mailjet.send = mock_send

            response = self.client.post(
                reverse("pages:contact-us"), data={"subject": "Test Subject"}
            )

            self.assertEqual(response.status_code, 200)
            mock_send.create.assert_not_called()

    def test_contact_us_post_empty_data(self):
        self.client.login(username="danitester", password="danitester")

        with patch("pages.views.mailjet") as mock_mailjet:
            mock_send = MagicMock()
            mock_mailjet.send = mock_send

            response = self.client.post(reverse("pages:contact-us"), data={})

            self.assertEqual(response.status_code, 200)
            mock_send.create.assert_not_called()

    def test_contact_us_mailjet_error(self):
        self.client.login(username="danitester", password="danitester")

        with patch("pages.views.mailjet") as mock_mailjet:
            mock_send = MagicMock()
            mock_send.create.side_effect = Exception("Mailjet API Error")
            mock_mailjet.send = mock_send

            response = self.client.post(
                reverse("pages:contact-us"), data=self.valid_data
            )

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "pages/contact-us.html")


class TestImportTradesView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.bg", password="danitester"
        )

        self.csv_content = [
            {
                "SYMBOL": "AAPL",
                "TYPE": "BUY",
                "AMOUNT": "100",
                "PRICE": "150.00",
                "DATETIME": "2023-01-01 10:00:00",
            },
            {
                "SYMBOL": "TSLA",
                "TYPE": "SELL",
                "AMOUNT": "50",
                "PRICE": "200.00",
                "DATETIME": "2023-01-02 11:00:00",
            },
        ]

    def create_csv_file(self, content):
        output = StringIO()
        writer = csv.DictWriter(
            output, fieldnames=["SYMBOL", "TYPE", "AMOUNT", "PRICE", "DATETIME"]
        )
        writer.writeheader()
        for row in content:
            writer.writerow(row)

        csv_file = SimpleUploadedFile(
            "trades.csv", output.getvalue().encode("utf-8"), content_type="text/csv"
        )
        return csv_file

    def test_import_trades_requires_login(self):
        response = self.client.post(reverse("pages:import-trades"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_import_trades_get_request(self):
        self.client.login(username="danitester", password="danitester")
        response = self.client.get(reverse("pages:import-trades"))
        self.assertEqual(response.status_code, 405)

    def test_import_trades_success(self):
        self.client.login(username="danitester", password="danitester")

        csv_file = self.create_csv_file(self.csv_content)

        response = self.client.post(
            reverse("pages:import-trades"), {"csv_file": csv_file}
        )

        self.assertRedirects(response, reverse("pages:profile"))
        trades = Trade.objects.filter(user=self.user)
        self.assertEqual(trades.count(), 2)

        aapl_trade = trades.get(ticker="AAPL")
        self.assertEqual(aapl_trade.trade_type, "BUY")
        self.assertEqual(aapl_trade.amount, Decimal("100"))
        self.assertEqual(aapl_trade.enter_price, Decimal("150.00"))

        tsla_trade = trades.get(ticker="TSLA")
        self.assertEqual(tsla_trade.trade_type, "SELL")
        self.assertEqual(tsla_trade.amount, Decimal("50"))
        self.assertEqual(tsla_trade.enter_price, Decimal("200.00"))
