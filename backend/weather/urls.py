"""
URLs for weather app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'weatherdatas', views.WeatherDataViewSet, basename='weatherdata')

urlpatterns = [
    path('', include(router.urls)),
]
