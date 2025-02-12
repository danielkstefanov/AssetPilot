from django.urls import path
from . import views

app_name = "markets"

urlpatterns = [
    path("", views.markets_home_view, name="markets-home-view"),
    path("search-stocks/", views.search_stocks, name="search-stocks"),
    path("create-strategy/", views.create_strategy, name="create_strategy"),
    path("get-strategy-details/<int:strategy_id>/", views.get_strategy_details,name="get_strategy_details"),
]
