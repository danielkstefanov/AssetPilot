from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("pages.urls")),
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
    path("markets/", include("markets.urls")),
    path("portfolio/", include("portfolio.urls")),
    path("news/", include("news.urls", namespace="news")),
]
