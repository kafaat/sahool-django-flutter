"""
URLs for iot app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'iotdevices', views.IoTDeviceViewSet, basename='iotdevice')
router.register(r'sensorreadings', views.SensorReadingViewSet, basename='sensorreading')

urlpatterns = [
    path('', include(router.urls)),
]
