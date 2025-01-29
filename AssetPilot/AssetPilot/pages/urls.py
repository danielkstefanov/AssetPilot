from django.urls import path
from . import views


app_name = "pages"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("profile/", views.profile, name="profile"),
    path("import-trades/", views.import_trades, name="import-trades"),
    path("contact-us/", views.contact_us_view, name="contact-us"),
]
