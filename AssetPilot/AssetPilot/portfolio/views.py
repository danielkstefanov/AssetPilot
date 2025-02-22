from openai import OpenAI
import os
import json

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from portfolio.constants import SUGGESTIONS_EXPLANATIONS, SYSTEM_EXPLANATION_FOR_PORTFOLIO_ANALYSIS, SYSTEM_EXPLANATION_FOR_TRADE_ANALYSIS
from markets.models import Trade
from utils.trading import get_ticker_price, get_pe_ratio, get_rsi

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@login_required
def portfolio(request):
    open_trades = Trade.objects.filter(user=request.user, is_open=True)

    open_trades_data = []
    try:
        for trade in open_trades:
            current_price = get_ticker_price(trade.ticker)
            enter_price = float(trade.enter_price)

            profit_loss_percentage = ((current_price - enter_price) / enter_price) * 100

            if trade.trade_type == "SELL":
                profit_loss_percentage *= -1

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
    except Exception as e:
        print(e)


@login_required
def portfolio_data(request):
    open_trades = Trade.objects.filter(user=request.user, is_open=True)
    total_value = 0
    allocation = {}
    protfolio_original_size = 0
    
    for trade in open_trades:
        current_price = get_ticker_price(trade.ticker)

        if trade.trade_type == "BUY":
            trade_value = float(trade.amount) * float(current_price)
        else:
            initial_value = float(trade.amount) * float(trade.enter_price)
            current_value = float(trade.amount) * float(current_price)
            trade_value = initial_value - (current_value - initial_value)
            
        total_value += trade_value
        protfolio_original_size += float(trade.amount) * float(trade.enter_price)
        
        if trade.ticker not in allocation:
            allocation[trade.ticker] = 0
        allocation[trade.ticker] += trade_value

    allocation_data = [
        {
            "symbol": ticker,
            "percentage": value / total_value * 100,
            "value": value,
        }
        for ticker, value in allocation.items()
    ]

    suggestions = create_suggestions(allocation)

    return JsonResponse(
        {
            "allocation": allocation_data,
            "suggestions": suggestions,
            "portfolio_value": total_value,
            "portfolio_return_percentage": (
                (total_value - protfolio_original_size) / protfolio_original_size
                * 100
                if protfolio_original_size != 0
                else 0
            ),
            "portfolio_return_value": total_value - protfolio_original_size,
        }
    )


def create_suggestions(allocation):

    suggestions = {
        "our_suggestions": [],
        "ai_suggestions": [],
    }

    suggestions["our_suggestions"] = get_our_suggestions(allocation)
    suggestions["ai_suggestions"] = get_ai_suggestions(allocation)

    return suggestions


def get_ai_suggestions(allocation):
    try:
        prompt = f"The allocation of the portfolio is: {", ".join([f"{ticker}: {percentage}%" for ticker, percentage in allocation.items()])}"
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_EXPLANATION_FOR_PORTFOLIO_ANALYSIS},
                {"role": "user", "content": prompt},
            ],
        )
        
        response_text = completion.choices[0].message.content
        response_json = json.loads(response_text)
        return response_json['suggestions']
    except Exception as e:
        print(e)

    return []


def get_our_suggestions(allocation):

    our_suggestions = []

    for suggestion in SUGGESTIONS_EXPLANATIONS:
        current_suggestion = suggestion["text"]
        to_add = False

        for ticker, percentage in allocation.items():
            pe_ratio = get_pe_ratio(ticker)
            rsi_value = get_rsi(ticker)

            if (pe_ratio is None and suggestion["indicator"] == "pe_ratio") or (rsi_value is None and suggestion["indicator"] == "rsi"):
                continue

            value_to_compare = {    
                "allocation": percentage,
                "pe_ratio": pe_ratio,
                "rsi": rsi_value,
            }[suggestion["indicator"]]

            if follows_suggestion(
                value_to_compare,
                suggestion["to_use_less_comparator"],
                suggestion["value"],
            ):
                current_suggestion += f"{ticker}, "
                to_add = True

        if to_add:
            our_suggestions.append(current_suggestion[:-2])

    return our_suggestions


def follows_suggestion(value_to_compare, to_use_less_comparator, value):
    if to_use_less_comparator:
        return value_to_compare < value
    else:
        return value_to_compare > value


@login_required
@require_POST
def close_trade(request, trade_id):
    try:
        trade = Trade.objects.get(id=trade_id, user=request.user)
        trade.close()
        return JsonResponse({
            'status': 'success',
            'message': 'Trade closed successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def trade_detail(request, trade_id):
    try:
        trade = get_object_or_404(Trade, id=trade_id, user=request.user)
    except Trade.DoesNotExist:
        return render(request, "portfolio/trade_detail.html", {"error": "Trade not found"})

    if trade.is_open:
        current_price = get_ticker_price(trade.ticker)
    else:
        current_price = float(trade.close_price)

    profit_loss = (
        (current_price - float(trade.enter_price)) / float(trade.enter_price)
    ) * 100

    if trade.trade_type == "SELL":
        profit_loss *= -1

    context = {
        "trade": trade,
        "current_price": round(current_price, 2),
        "profit_loss": round(profit_loss, 2),
        "profit_loss_amount": round(
            (profit_loss / 100 * float(trade.enter_price)) * float(trade.amount), 2
        ),
        "enter_date": trade.enter_date,
        "close_date": trade.close_date,
        "ai_analysis": ai_analysis_for_trade(trade),
    }

    return render(request, "portfolio/trade_detail.html", context)


def ai_analysis_for_trade(trade):

    prompt = f"The trade is: {trade.ticker} {trade.trade_type} {trade.amount} at {trade.enter_price} on {trade.enter_date}"
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_EXPLANATION_FOR_TRADE_ANALYSIS},
            {"role": "user", "content": prompt},
        ],
    )   

    response_text = completion.choices[0].message.content
    response_json = json.loads(response_text)
    
    return response_json['explanation'] + "\n" + response_json['suggestion']

@login_required
def get_trade_strategy(request, trade_id):
    try:
        trade = Trade.objects.get(id=trade_id, user=request.user)
        
        if trade.strategy:
            strategy = {
                "title": trade.strategy.title,
                "enter_position_explanation": trade.strategy.enter_position_explanation,
                "trade_exit_explanation": trade.strategy.trade_exit_explanation,
            }
            return JsonResponse({ "status": "success", "strategy": strategy})
        else:
            return JsonResponse({ "status": "success", "strategy": None})
            
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=500)
