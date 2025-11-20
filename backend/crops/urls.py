"""
URLs for crops app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'crops', views.CropViewSet, basename='crop')

urlpatterns = [
    path('', include(router.urls)),
]
