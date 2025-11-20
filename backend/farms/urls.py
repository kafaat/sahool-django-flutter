"""
URLs for farms app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'farms', views.FarmViewSet, basename='farm')

urlpatterns = [
    path('', include(router.urls)),
]
