# TradingPro\TradingPro\urls.py
from django.urls import path, include

urlpatterns = [
    # ... other url patterns ...
    path('', include('InsiderApp.urls')),
]
