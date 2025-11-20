"""
Views for weather app.
"""

from rest_framework import viewsets, permissions
from .models import WeatherData
from .serializers import WeatherDataSerializer


class WeatherDataViewSet(viewsets.ModelViewSet):
    """
    ViewSet for WeatherData model.
    """
    queryset = WeatherData.objects.all()
    serializer_class = WeatherDataSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


