"""
URLs for users app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # Authentication endpoints
    path('login/', obtain_auth_token, name='api_token_auth'),
]
