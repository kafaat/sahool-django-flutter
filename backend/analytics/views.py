"""
Views for analytics app.
"""

from rest_framework import viewsets, permissions
from .models import FarmAnalytics
from .serializers import FarmAnalyticsSerializer


class FarmAnalyticsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for FarmAnalytics model.
    """
    queryset = FarmAnalytics.objects.all()
    serializer_class = FarmAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


