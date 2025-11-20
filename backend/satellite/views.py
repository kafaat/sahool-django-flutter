"""
Views for satellite app.
"""

from rest_framework import viewsets, permissions
from .models import SatelliteImage
from .serializers import SatelliteImageSerializer


class SatelliteImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SatelliteImage model.
    """
    queryset = SatelliteImage.objects.all()
    serializer_class = SatelliteImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


