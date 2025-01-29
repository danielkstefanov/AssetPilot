from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from markets.models import Trade
from utils.trading import get_ticker_price


@login_required
def portfolio(request):
    open_trades = Trade.objects.filter(user=request.user, is_open=True)

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

    return render(
        request, "portfolio/portfolio.html", {"open_trades_data": open_trades_data}
    )


@login_required
def portfolio_data(request):
    open_trades = Trade.objects.filter(user=request.user, is_open=True)
    total_value = sum(
        float(trade.amount) * float(get_ticker_price(trade.ticker))
        for trade in open_trades
    )

    allocation = {}
    protfolio_original_size = 0

    for trade in open_trades:
        trade_value = float(trade.amount) * float(get_ticker_price(trade.ticker))
        protfolio_original_size += float(trade.amount) * float(trade.enter_price)
        if trade.ticker not in allocation:
            allocation[trade.ticker] = 0
        allocation[trade.ticker] += trade_value / total_value * 100

    allocation_data = [
        {
            "symbol": ticker,
            "percentage": percentage,
            "value": (percentage / 100) * total_value,
        }
        for ticker, percentage in allocation.items()
    ]

    suggestions = []
    for symbol, percentage in allocation.items():
        if percentage > 20:
            suggestions.append(f"You have too much allocation in {symbol}")

    return JsonResponse(
        {
            "allocation": allocation_data,
            "suggestions": suggestions,
            "portfolio_value": total_value,
            "portfolio_return_percentage": (total_value - protfolio_original_size)
            / protfolio_original_size
            * 100,
            "portfolio_return_value": total_value - protfolio_original_size,
        }
    )


@login_required
@require_POST
def close_trade(request, trade_id):
    trade = Trade.objects.get(id=trade_id, user=request.user)
    trade.close()


@login_required
def trade_detail(request, trade_id):
    trade = Trade.objects.get(id=trade_id, user=request.user)

    if trade.is_open:
        current_price = get_ticker_price(trade.ticker)
    else:
        current_price = float(trade.close_price)

    profit_loss = (
        (current_price - float(trade.enter_price)) / float(trade.enter_price)
    ) * 100

    context = {
        "trade": trade,
        "current_price": round(current_price, 2),
        "profit_loss": round(profit_loss, 2),
        "profit_loss_amount": round(
            (profit_loss / 100 * float(trade.enter_price)) * float(trade.amount), 2
        ),
        "enter_date": trade.enter_date,
        "close_date": trade.close_date,
        "ai_analysis": [],
    }

    return render(request, "portfolio/trade_detail.html", context)
