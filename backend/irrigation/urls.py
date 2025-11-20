"""
URLs for irrigation app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'irrigationschedules', views.IrrigationScheduleViewSet, basename='irrigationschedule')

urlpatterns = [
    path('', include(router.urls)),
]
