"""
Views for fields app.
"""

from rest_framework import viewsets, permissions
from .models import Field
from .serializers import FieldSerializer


class FieldViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Field model.
    """
    queryset = Field.objects.all()
    serializer_class = FieldSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


