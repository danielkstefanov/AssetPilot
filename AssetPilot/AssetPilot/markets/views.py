import os
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Trade
import finnhub
from django.conf import settings

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
finnhub_client = finnhub.Client(FINNHUB_API_KEY)


@login_required
def markets_home_view(request):
    ticker = request.GET.get("q", "AAPL")

    if request.method == "POST":
        try:
            trade_type = request.POST.get("order_type").upper()
            amount = request.POST.get("amount")

            quote = finnhub_client.quote(ticker)
            current_price = quote["c"]

            Trade.objects.create(
                user=request.user,
                ticker=ticker,
                trade_type=trade_type,
                amount=amount,
                price=current_price,
            )

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
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
