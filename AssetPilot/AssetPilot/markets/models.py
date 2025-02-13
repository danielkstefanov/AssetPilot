from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from utils.trading import get_ticker_price


class Strategy(models.Model):
    title = models.CharField(max_length=200)
    enter_position_explanation = models.TextField()
    trade_exit_explanation = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)


class Trade(models.Model):
    TRADE_TYPES = [
        ("BUY", "Buy"),
        ("SELL", "Sell"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    strategy = models.ForeignKey(
        Strategy, on_delete=models.SET_NULL, null=True, blank=True
    )
    ticker = models.CharField(max_length=10)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    enter_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    enter_date = models.DateTimeField()
    close_date = models.DateTimeField(null=True, blank=True)
    is_open = models.BooleanField(default=True)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(enter_price__gt=0),
                name="enter_price_must_be_greater_than_0",
            ),
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name="amount_must_be_greater_than_0",
            ),
            models.CheckConstraint(
                check=models.Q(enter_date__lte=datetime.now()),
                name="enter_date_must_be_in_the_past",
            ),
        ]

    def close(self):
        self.is_open = False
        self.close_price = get_ticker_price(self.ticker)
        self.close_date = datetime.now()
        self.save()
