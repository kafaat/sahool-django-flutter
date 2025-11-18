from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import IoTDevice, Sensor, Actuator, SensorReading
from .serializers import (
    IoTDeviceSerializer,
    IoTDeviceDetailSerializer,
    SensorSerializer,
    ActuatorSerializer,
    SensorReadingSerializer
)


class IoTDeviceViewSet(viewsets.ModelViewSet):
    queryset = IoTDevice.objects.all()
    serializer_class = IoTDeviceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['field', 'device_type', 'status']
    search_fields = ['name', 'device_id']
    ordering_fields = ['created_at', 'last_seen', 'battery_level']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return IoTDeviceDetailSerializer
        return IoTDeviceSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return IoTDevice.objects.all()
        return IoTDevice.objects.filter(field__farm__owner=user)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """تحديث حالة الجهاز"""
        device = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['online', 'offline', 'maintenance']:
            return Response(
                {'error': 'حالة غير صالحة'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        device.status = new_status
        device.last_seen = timezone.now()
        device.save()
        return Response({'message': 'تم تحديث حالة الجهاز'})


class SensorViewSet(viewsets.ModelViewSet):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['device', 'sensor_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Sensor.objects.all()
        return Sensor.objects.filter(device__field__farm__owner=user)
    
    @action(detail=True, methods=['get'])
    def readings(self, request, pk=None):
        """الحصول على قراءات المستشعر"""
        sensor = self.get_object()
        limit = int(request.query_params.get('limit', 100))
        readings = sensor.readings.order_by('-timestamp')[:limit]
        serializer = SensorReadingSerializer(readings, many=True)
        return Response(serializer.data)


class ActuatorViewSet(viewsets.ModelViewSet):
    queryset = Actuator.objects.all()
    serializer_class = ActuatorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['device', 'actuator_type', 'status']
    ordering_fields = ['created_at', 'last_activated']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Actuator.objects.all()
        return Actuator.objects.filter(device__field__farm__owner=user)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """تفعيل المشغل"""
        actuator = self.get_object()
        actuator.status = 'on'
        actuator.last_activated = timezone.now()
        actuator.save()
        return Response({'message': 'تم تفعيل المشغل'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """إيقاف المشغل"""
        actuator = self.get_object()
        actuator.status = 'off'
        actuator.save()
        return Response({'message': 'تم إيقاف المشغل'})


class SensorReadingViewSet(viewsets.ModelViewSet):
    queryset = SensorReading.objects.all()
    serializer_class = SensorReadingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['sensor']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return SensorReading.objects.all()
        return SensorReading.objects.filter(sensor__device__field__farm__owner=user)
