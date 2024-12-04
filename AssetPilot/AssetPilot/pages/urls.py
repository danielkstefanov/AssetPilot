from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('contact-us/', views.contact_us_view, name='contact-us'),
]
