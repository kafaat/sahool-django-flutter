"""
URLs for satellite app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'satelliteimages', views.SatelliteImageViewSet, basename='satelliteimage')

urlpatterns = [
    path('', include(router.urls)),
]
