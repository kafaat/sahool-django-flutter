"""
Views for crops app.
"""

from rest_framework import viewsets, permissions
from .models import Crop
from .serializers import CropSerializer


class CropViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Crop model.
    """
    queryset = Crop.objects.all()
    serializer_class = CropSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


