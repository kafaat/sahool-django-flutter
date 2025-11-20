"""
Views for irrigation app.
"""

from rest_framework import viewsets, permissions
from .models import IrrigationSchedule
from .serializers import IrrigationScheduleSerializer


class IrrigationScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for IrrigationSchedule model.
    """
    queryset = IrrigationSchedule.objects.all()
    serializer_class = IrrigationScheduleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


