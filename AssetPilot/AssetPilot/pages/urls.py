from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),          # Home page
    path('about/', views.about_view, name='about'),  # About page
    path('contact/', views.contact_view, name='contact'),  # Contact page
]
