import os
import finnhub
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Trade
from utils.trading import get_ticker_price


FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
finnhub_client = finnhub.Client(FINNHUB_API_KEY)


@login_required
def markets_home_view(request):
    ticker = request.GET.get("q", "AAPL").upper()

    if request.method == "POST":
        trade_type = request.POST.get("order_type").upper()
        amount = request.POST.get("amount")

        current_price = get_ticker_price(ticker)

        Trade.objects.create(
            user=request.user,
            ticker=ticker,
            trade_type=trade_type,
            amount=amount,
            price=current_price,
        )
    elif request.method == "GET":
        context = {"search_query": ticker}
        return render(request, "markets/markets.html", context)


def search_stocks(request):
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
