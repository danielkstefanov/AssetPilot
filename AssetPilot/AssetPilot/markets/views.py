from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Trade
import yfinance as yf


@login_required
def markets_home_view(request):

    ticker = request.GET.get("q", "AAPL")

    if request.method == "POST":
        trade_type = request.POST.get("order_type").upper()
        amount = request.POST.get("amount")

        stock = yf.Ticker(ticker)
        current_price = stock.fast_info["lastPrice"]

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
    query = request.GET.get("q", "").upper()
    if len(query) < 2:
        return JsonResponse([], safe=False)

    search_results = yf.Tickers(query)
    results = []

    for result in search_results:

        try:
            ticker = yf.Ticker(result)
            info = ticker.info
            results.append({"symbol": result, "name": info.get("longName", "")})
        except:
            continue

        if len(results) >= 10:
            break

    return JsonResponse(results, safe=False)
