"""
URLs for analytics app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'farmanalyticss', views.FarmAnalyticsViewSet, basename='farmanalytics')

urlpatterns = [
    path('', include(router.urls)),
]
