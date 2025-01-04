import finnhub
import os
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from markets.models import Trade
from utils.trading import get_ticker_price
import yfinance as yf
from datetime import datetime, timedelta

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
finnhub_client = finnhub.Client(FINNHUB_API_KEY)


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

    for trade in open_trades:
        trade_value = float(trade.amount) * float(get_ticker_price(trade.ticker))
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
    trade.close_price = get_ticker_price(trade.ticker)
    trade.close_date = datetime.now()
    trade.close()


@login_required
def trade_detail(request, trade_id):
    trade = Trade.objects.get(id=trade_id, user=request.user)

    current_price = get_ticker_price(trade.ticker)
    profit_loss = (
        (current_price - float(trade.enter_price)) / float(trade.enter_price)
    ) * 100

    context = {
        "trade": trade,
        "current_price": round(current_price, 2),
        "profit_loss": round(profit_loss, 2),
        "ai_analysis": [],
    }

    return render(request, "portfolio/trade_detail.html", context)
    # ticker = yf.Ticker(trade.ticker)
    # if ticker is None:
    # else:
    #     hist = ticker.history(period="1mo")
    #     ai_analysis = []
    #     if len(hist) >= 14:
    #         delta = hist["Close"].diff()
    #         gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    #         loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    #         rs = gain / loss
    #         rsi = 100 - (100 / (1 + rs.iloc[-1]))

    #         if rsi > 70:
    #             ai_analysis.append(
    #                 f"The RSI is {round(rsi, 2)} which indicates that {trade.ticker} might be overbought"
    #             )
    #         elif rsi < 30:
    #             ai_analysis.append(
    #                 f"The RSI is {round(rsi, 2)} which indicates that {trade.ticker} might be oversold"
    #             )

    #     ma20 = hist["Close"].rolling(window=20).mean().iloc[-1]
    #     current_price = hist["Close"].iloc[-1]

    #     if current_price > ma20:
    #         ai_analysis.append(
    #             f"Price is above 20-day moving average, suggesting an upward trend"
    #         )
    #     else:
    #         ai_analysis.append(
    #             f"Price is below 20-day moving average, suggesting a downward trend"
    #         )

    #     avg_volume = hist["Volume"].mean()
    #     last_volume = hist["Volume"].iloc[-1]

    #     if last_volume > avg_volume * 1.5:
    #         ai_analysis.append("Trading volume is significantly higher than average")
