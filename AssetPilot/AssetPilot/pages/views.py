import os
from django.shortcuts import render, redirect
from django.contrib import messages
from mailjet_rest import Client
from django.contrib.auth.decorators import login_required
from markets.models import Trade
from utils.trading import get_ticker_price

MAILJET_API_KEY = os.environ.get("MAILJET_API_KEY")
MAILJET_API_SECRET = os.environ.get("MAILJET_API_SECRET")
MAILJET_EMAIL = os.environ.get("MAILJET_EMAIL")


def error_404_view(request, exception):
    return render(request, "404.html", status=404)


def home_view(request):
    return render(request, "pages/home.html")


@login_required
def profile(request):
    open_trades = Trade.objects.filter(user=request.user, is_open=True)
    trade_history = Trade.objects.filter(user=request.user, is_open=False)

    open_trades_data = []
    for trade in open_trades:
        current_price = get_ticker_price(trade.ticker)
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

    strategies = [
        {"name": "Standard Deviation Strategy"},
        {"name": "Moving Average Strategy"},
        {"name": "Bullish Crypto Strategy"},
    ]

    context = {
        "user": request.user,
        "open_trades_data": open_trades_data,
        "closed_trades_data": closed_trades_data,
        "strategies": strategies,
    }

    return render(request, "pages/profile.html", context)


def contact_us_view(request):
    if request.method == "POST":

        if not request.user.is_authenticated:
            return render(
                request, "pages/contact-us.html", {"error": "You have to be logged in!"}
            )

        subject = request.POST.get("subject")
        message = request.POST.get("message")
        user_email = request.user.email

        if subject and message:
            mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version="v3.1")
            data = {
                "Messages": [
                    {
                        "From": {"Email": MAILJET_EMAIL, "Name": "Asset Pilot"},
                        "To": [{"Email": MAILJET_EMAIL, "Name": "Support Team"}],
                        "Subject": subject,
                        "TextPart": f"Message from {user_email}:\n\n{message}",
                    }
                ]
            }
            result = mailjet.send.create(data=data)

            if result.status_code == 200:
                messages.success(request, "Your message has been sent successfully!")
            else:
                messages.error(
                    request, "Failed to send your message. Please try again later."
                )

            return redirect("contact-us")

    return render(request, "pages/contact-us.html")
