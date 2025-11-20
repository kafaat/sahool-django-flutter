"""
URLs for ai app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'diseasedetections', views.DiseaseDetectionViewSet, basename='diseasedetection')

urlpatterns = [
    path('', include(router.urls)),
]
