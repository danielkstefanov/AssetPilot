from django.contrib import admin
from django.urls import path, include
from pages.views import error_404_view

urlpatterns = [
    path("", include("pages.urls")),
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
    path("markets/", include("markets.urls")),
    path("portfolio/", include("portfolio.urls")),
]

handler404 = "pages.views.error_404_view"
