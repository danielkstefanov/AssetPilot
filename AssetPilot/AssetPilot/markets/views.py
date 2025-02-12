import os
import finnhub
import json

from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Trade, Strategy
from utils.trading import get_ticker_price
from datetime import datetime


FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
finnhub_client = finnhub.Client(FINNHUB_API_KEY)


@login_required
def markets_home_view(request):
    ticker = request.GET.get("q", "AAPL").upper()

    if request.method == "POST":
        trade_type = request.POST.get("order_type").upper()
        amount = request.POST.get("amount")

        strategy = request.POST.get("strategy")
        if strategy != "default":
            strategy = Strategy.objects.get(id=strategy, creator=request.user)
        else:
            strategy = None

        current_price = get_ticker_price(ticker)

        trade = Trade.objects.create(
            user=request.user,
            ticker=ticker,
            trade_type=trade_type,
            amount=amount,
            enter_price=current_price,
            enter_date=datetime.now(),
            strategy=strategy,
        )

        return JsonResponse(
            {
                "status": "success",
                "trade": {
                    "trade_id": trade.id,
                    "ticker": trade.ticker,
                    "amount": trade.amount,
                    "trade_type": trade.trade_type,
                    "enter_price": trade.enter_price,
                    "enter_date": trade.enter_date,
                },
            }
        )
    elif request.method == "GET":
        open_trades = Trade.objects.filter(user=request.user, is_open=True)
        strategies = Strategy.objects.filter(creator=request.user)

        open_trades_data = []
        for trade in filter(lambda trade: trade.ticker == ticker, open_trades):
            try:
                current_price = get_ticker_price(trade.ticker)
            except:
                return redirect("markets_home")

            enter_price = float(trade.enter_price)

            profit_loss_percentage = ((current_price - enter_price) / enter_price) * 100

            open_trades_data.append(
                {
                    "id": trade.id,
                    "ticker": trade.ticker,
                    "amount": trade.amount,
                    "enter_price": trade.enter_price,
                    "trade_type": trade.trade_type,
                    "profit_loss_percentage": round(profit_loss_percentage, 2),
                }
            )

        context = {
            "search_query": ticker,
            "open_trades_data": open_trades_data,
            "strategies": strategies,
        }

        return render(request, "markets/markets.html", context)


def search_stocks(request):
    try:
        query = request.GET.get("q", "").strip()
        if len(query) < 2:
            return JsonResponse([], safe=False)

        search_results = finnhub_client.symbol_lookup(query)

        results = []

        for item in search_results.get("result", [])[:10]:
            if item.get("type") == "Common Stock":
                results.append(
                    {
                        "symbol": item.get("symbol", ""),
                        "name": item.get("description", ""),
                    }
                )

        return JsonResponse(results, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@login_required
def create_strategy(request):
    try:
        data = json.loads(request.body)

        strategy = Strategy.objects.create(
            title=data.get("title"),
            enter_position_explanation=data.get("enter_position_explanation"),
            trade_exit_explanation=data.get("trade_exit_explanation"),
            creator=request.user,
        )

        return JsonResponse(
            {
                "id": strategy.id,
                "title": strategy.title,
                "enter_position_explanation": strategy.enter_position_explanation,
                "trade_exit_explanation": strategy.trade_exit_explanation,
                "creator": strategy.creator.username,
            }
        )
    except:
        return JsonResponse({"error": "Failed to create strategy"}, status=400)


@login_required
def get_strategy_details(request, strategy_id):
    try:
        strategy = Strategy.objects.get(id=strategy_id, creator=request.user)

        return JsonResponse(
            {
                "title": strategy.title,
                "enter_position_explanation": strategy.enter_position_explanation,
                "trade_exit_explanation": strategy.trade_exit_explanation,
            }
        )
    except Strategy.DoesNotExist:
        return JsonResponse({"error": "Strategy not found"}, status=404)
