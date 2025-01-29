from django.urls import path
from . import views

app_name = "portfolio"

urlpatterns = [
    path("", views.portfolio, name="portfolio"),
    path("data/", views.portfolio_data, name="portfolio_data"),
    path("close-trade/<int:trade_id>/", views.close_trade, name="close_trade"),
    path("trade/<int:trade_id>/", views.trade_detail, name="trade_detail"),
]
