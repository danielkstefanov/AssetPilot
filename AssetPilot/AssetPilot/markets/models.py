from django.db import models
from django.contrib.auth.models import User


class Watchlist(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="watchlist"
    )
    created_at = models.DateTimeField(auto_now_add=True)


class WatchlistItem(models.Model):
    watchlist = models.ForeignKey(
        Watchlist, on_delete=models.CASCADE, related_name="items"
    )
    stock_symbol = models.CharField(max_length=10)
    added_at = models.DateTimeField(auto_now_add=True)


class Trade(models.Model):
    TRADE_TYPES = [
        ("BUY", "Buy"),
        ("SELL", "Sell"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_open = models.BooleanField(default=True)

    def close_trade(self):
        self.is_open = False
        self.save()
