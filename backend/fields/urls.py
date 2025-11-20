"""
URLs for fields app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'fields', views.FieldViewSet, basename='field')

urlpatterns = [
    path('', include(router.urls)),
]
