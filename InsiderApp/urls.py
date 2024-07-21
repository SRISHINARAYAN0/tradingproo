# TradingPro/InsiderApp/urls.py
from django.urls import path
from .views import InsiderTrackingView

urlpatterns = [
    path("", InsiderTrackingView.as_view(), name="homepage"),
]
