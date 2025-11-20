"""
Views for ai app.
"""

from rest_framework import viewsets, permissions
from .models import DiseaseDetection
from .serializers import DiseaseDetectionSerializer


class DiseaseDetectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DiseaseDetection model.
    """
    queryset = DiseaseDetection.objects.all()
    serializer_class = DiseaseDetectionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


