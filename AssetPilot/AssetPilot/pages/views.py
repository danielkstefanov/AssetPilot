import os
from django.shortcuts import render, redirect
from django.contrib import messages
from mailjet_rest import Client
from django.contrib.auth.decorators import login_required
from markets.models import Trade, Strategy
from utils.trading import get_ticker_price
import csv
from io import TextIOWrapper
from django.http import JsonResponse
from django.views.decorators.http import require_POST

MAILJET_API_KEY = os.environ.get("MAILJET_API_KEY")
MAILJET_API_SECRET = os.environ.get("MAILJET_API_SECRET")
MAILJET_EMAIL = os.environ.get("MAILJET_EMAIL")
mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version="v3.1")


def home_view(request):
    return render(request, "pages/home.html")


@login_required
def profile(request):
    open_trades = Trade.objects.filter(user=request.user, is_open=True)
    trade_history = Trade.objects.filter(user=request.user, is_open=False)
    strategies = Strategy.objects.filter(creator=request.user)

    open_trades_data = []
    for trade in open_trades:
        try:
            current_price = get_ticker_price(trade.ticker)
        except Exception as e:
            current_price = 0
        enter_price = float(trade.enter_price)

        profit_loss_percentage = ((current_price - enter_price) / enter_price) * 100

        open_trades_data.append(
            {
                "id": trade.id,
                "ticker": trade.ticker,
                "amount": trade.amount,
                "enter_price": trade.enter_price,
                "current_price": current_price,
                "trade_type": trade.trade_type,
                "profit_loss_percentage": round(profit_loss_percentage, 2),
            }
        )

    closed_trades_data = []
    for trade in trade_history:
        enter_price = float(trade.enter_price)
        close_price = float(trade.close_price)

        profit_loss_percentage = ((close_price - enter_price) / enter_price) * 100

        closed_trades_data.append(
            {
                "id": trade.id,
                "ticker": trade.ticker,
                "amount": trade.amount,
                "enter_price": trade.enter_price,
                "close_price": trade.close_price,
                "trade_type": trade.trade_type,
                "profit_loss_percentage": round(profit_loss_percentage, 2),
            }
        )

    context = {
        "user": request.user,
        "open_trades_data": open_trades_data,
        "closed_trades_data": closed_trades_data,
        "strategies": strategies,
    }

    return render(request, "pages/profile.html", context)


@login_required
def contact_us_view(request):
    if request.method == "POST":

        subject = request.POST.get("subject")
        message = request.POST.get("message")
        user_email = request.user.email

        if subject and message:
            try:
                mailjet.send.create(
                    data={
                        "Messages": [
                            {
                                "From": {"Email": user_email, "Name": "Asset Pilot"},
                                "To": [
                                    {"Email": MAILJET_EMAIL, "Name": "Support Team"}
                                ],
                                "Subject": subject,
                                "TextPart": f"Message from {user_email}:\n\n{message}",
                            }
                        ]
                    }
                )
            except Exception as e:
                print(e)

    return render(request, "pages/contact-us.html")


@login_required
@require_POST
def import_trades(request):
    if request.method == "POST":
        csv_file = request.FILES["csv_file"]
        text_file = TextIOWrapper(csv_file, encoding="utf-8")
        csv_reader = csv.DictReader(text_file)

        for row in csv_reader:
            Trade.objects.create(
                user=request.user,
                ticker=row["SYMBOL"],
                trade_type=row["TYPE"],
                amount=row["AMOUNT"],
                enter_price=row["PRICE"],
                enter_date=row["DATETIME"],
                strategy=None,
            )

    return redirect("pages:profile")
