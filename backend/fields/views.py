from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Field, IrrigationSchedule
from .serializers import (
    FieldSerializer, 
    FieldDetailSerializer,
    IrrigationScheduleSerializer
)


class FieldViewSet(viewsets.ModelViewSet):
    queryset = Field.objects.all()
    serializer_class = FieldSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['farm', 'crop', 'soil_type', 'status']
    search_fields = ['name', 'notes']
    ordering_fields = ['created_at', 'name', 'area', 'planting_date']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FieldDetailSerializer
        return FieldSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Field.objects.all()
        return Field.objects.filter(farm__owner=user)
    
    @action(detail=True, methods=['get'])
    def health_status(self, request, pk=None):
        """حالة صحة الحقل"""
        field = self.get_object()
        # يمكن إضافة منطق معقد لحساب صحة الحقل
        health_data = {
            'field_id': field.id,
            'field_name': field.name,
            'status': field.status,
            'devices_active': field.devices.filter(status='online').count(),
            'devices_total': field.devices.count(),
            'last_irrigation': field.irrigation_schedules.filter(
                status='completed'
            ).order_by('-completed_at').first(),
        }
        return Response(health_data)


class IrrigationScheduleViewSet(viewsets.ModelViewSet):
    queryset = IrrigationSchedule.objects.all()
    serializer_class = IrrigationScheduleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['field', 'status']
    ordering_fields = ['scheduled_time', 'created_at']
    ordering = ['-scheduled_time']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return IrrigationSchedule.objects.all()
        return IrrigationSchedule.objects.filter(field__farm__owner=user)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """تحديد جدولة الري كمكتملة"""
        schedule = self.get_object()
        if schedule.status == 'completed':
            return Response(
                {'error': 'الجدولة مكتملة بالفعل'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        schedule.status = 'completed'
        schedule.save()
        return Response({'message': 'تم تحديث حالة الجدولة'})
