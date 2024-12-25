import finnhub
import os
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from markets.models import Trade
from utils.trading import get_ticker_price

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
finnhub_client = finnhub.Client(FINNHUB_API_KEY)


@login_required
def portfolio(request):
    open_trades = Trade.objects.filter(user=request.user, is_open=True)

    open_trades_data = []
    for trade in open_trades:
        current_price = get_ticker_price(trade.ticker)
        enter_price = float(trade.price)

        profit_loss_percentage = ((current_price - enter_price) / enter_price) * 100

        open_trades_data.append(
            {
                "id": trade.id,
                "ticker": trade.ticker,
                "amount": trade.amount,
                "price": trade.price,
                "trade_type": trade.trade_type,
                "profit_loss_percentage": round(profit_loss_percentage, 2),
            }
        )

    return render(
        request, "portfolio/portfolio.html", {"open_trades_data": open_trades_data}
    )


@login_required
def portfolio_data(request):
    open_trades = Trade.objects.filter(user=request.user, is_open=True)
    total_value = sum(trade.amount * trade.price for trade in open_trades)

    allocation = {}

    for trade in open_trades:
        trade_value = trade.amount * trade.price
        if trade.ticker not in allocation:
            allocation[trade.ticker] = 0
        allocation[trade.ticker] += trade_value / total_value * 100

    allocation_data = [
        {"symbol": ticker, "percentage": percentage}
        for ticker, percentage in allocation.items()
    ]

    suggestions = []
    for symbol, percentage in allocation.items():
        if percentage > 20:
            suggestions.append(f"You have too much allocation in {symbol}")

    return JsonResponse({"allocation": allocation_data, "suggestions": suggestions})


@login_required
@require_POST
def close_trade(request, trade_id):
    trade = Trade.objects.get(id=trade_id, user=request.user)
    trade.close()
