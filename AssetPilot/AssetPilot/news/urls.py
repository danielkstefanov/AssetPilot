from django.urls import path
from . import views

app_name = "news"

urlpatterns = [
    path("", views.news, name="news"),
    path("details/<str:news_headline>/", views.news_details, name="news_details"),
]
