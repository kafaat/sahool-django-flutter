"""
Views for iot app.
"""

from rest_framework import viewsets, permissions
from .models import IoTDevice, SensorReading
from .serializers import IoTDeviceSerializer, SensorReadingSerializer


class IoTDeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for IoTDevice model.
    """
    queryset = IoTDevice.objects.all()
    serializer_class = IoTDeviceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SensorReadingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SensorReading model.
    """
    queryset = SensorReading.objects.all()
    serializer_class = SensorReadingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


