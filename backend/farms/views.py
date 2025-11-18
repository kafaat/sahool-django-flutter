from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Farm, Crop
from .serializers import FarmSerializer, FarmDetailSerializer, CropSerializer


class FarmViewSet(viewsets.ModelViewSet):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['owner']
    search_fields = ['name', 'location', 'description']
    ordering_fields = ['created_at', 'name', 'total_area']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FarmDetailSerializer
        return FarmSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Farm.objects.all()
        return Farm.objects.filter(owner=user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """إحصائيات المزرعة"""
        farm = self.get_object()
        stats = {
            'total_fields': farm.fields.count(),
            'total_area': farm.total_area,
            'active_fields': farm.fields.filter(status='active').count(),
            'total_devices': sum(field.devices.count() for field in farm.fields.all()),
        }
        return Response(stats)


class CropViewSet(viewsets.ModelViewSet):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'variety']
    ordering_fields = ['name', 'growth_duration']
    ordering = ['name']
