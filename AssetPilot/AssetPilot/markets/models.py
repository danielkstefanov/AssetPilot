from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from utils.trading import get_ticker_price


class Trade(models.Model):
    TRADE_TYPES = [
        ("BUY", "Buy"),
        ("SELL", "Sell"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    enter_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    enter_date = models.DateTimeField(auto_now_add=True)
    close_date = models.DateTimeField(null=True, blank=True)
    is_open = models.BooleanField(default=True)

    def close(self):
        self.is_open = False
        self.close_price = get_ticker_price(self.ticker)
        self.close_date = datetime.now()
        self.save()
