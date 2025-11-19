"""
API Views للتحليلات المتقدمة - التكامل الشامل
Advanced Analytics API Views - Comprehensive Integration
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db.models import Avg, Sum, Count, Q, F
from django.db.models.functions import TruncDate, TruncHour, TruncMonth
from datetime import timedelta, datetime
import json

from .models import (
    FarmAnalytics, CropAnalytics, IoTAnalytics, 
    FinancialAnalytics, WeatherAnalytics, MarketAnalytics
)
from .serializers import (
    FarmAnalyticsSerializer, CropAnalyticsSerializer, IoTAnalyticsSerializer,
    FinancialAnalyticsSerializer, WeatherAnalyticsSerializer, MarketAnalyticsSerializer
)
from apps.farms.models import Farm, Crop, CropCalendar
from apps.iot.models import IoTDevice, SensorReading
from apps.marketplace.models import CropListing, Transaction
from .services import AnalyticsService, PredictionService


class FarmAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet لتحليلات المزارع"""
    
    queryset = FarmAnalytics.objects.all()
    serializer_class = FarmAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['farm', 'date', 'metric_type']
    search_fields = ['farm__name', 'metric_type']
    ordering_fields = ['date', 'value', 'created_at']
    
    def get_queryset(self):
        return self.queryset.filter(farm__owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """ملخص لوحة التحكم الرئيسية"""
        user = request.user
        farms = Farm.objects.filter(owner=user, is_active=True)
        
        # الإحصائيات العامة
        total_farms = farms.count()
        total_area = farms.aggregate(total=Sum('area_hectares'))['total'] or 0
        total_crops = Crop.objects.filter(farm__owner=user).count()
        total_devices = IoTDevice.objects.filter(farm__owner=user, is_active=True).count()
        
        # المزارع النشطة
        active_farms = farms.filter(status='active').count()
        
        # إجمالي الاستثمار
        total_investment = farms.aggregate(total=Sum('total_investment'))['total'] or 0
        
        # متوسط الكفاءة
        avg_water_efficiency = farms.aggregate(avg=Avg('water_efficiency'))['avg'] or 0
        avg_productivity = farms.aggregate(avg=Avg('productivity_index'))['avg'] or 0
        
        # المحاصيل حسب الحالة
        crop_statuses = Crop.objects.filter(farm__owner=user).values('status').annotate(
            count=Count('status')
        )
        
        # أجهزة IoT حسب الحالة
        device_statuses = IoTDevice.objects.filter(farm__owner=user).values('status').annotate(
            count=Count('status')
        )
        
        data = {
            'total_farms': total_farms,
            'active_farms': active_farms,
            'total_area_hectares': float(total_area),
            'total_crops': total_crops,
            'total_devices': total_devices,
            'total_investment': float(total_investment),
            'avg_water_efficiency': float(avg_water_efficiency),
            'avg_productivity_index': float(avg_productivity),
            'crop_status_distribution': list(crop_statuses),
            'device_status_distribution': list(device_statuses),
            'farms_list': [
                {
                    'id': farm.id,
                    'name': farm.name,
                    'type': farm.type,
                    'area_hectares': float(farm.area_hectares),
                    'status': farm.status,
                    'total_crops': farm.total_crops,
                    'total_devices': farm.total_iot_devices,
                    'water_efficiency': float(farm.water_efficiency),
                    'productivity_index': float(farm.productivity_index),
                    'rating': float(farm.rating),
                }
                for farm in farms[:10]  # أول 10 مزارع
            ]
        }
        
        return Response(data)
    
    @action(detail=True, methods=['get'])
    def farm_detailed_analytics(self, request, pk=None):
        """تحليلات مفصلة لمزرعة محددة"""
        farm = self.get_object().farm
        
        if farm.owner != request.user:
            return Response({'error': 'ليس لديك صلاحية'}, status=status.HTTP_403_FORBIDDEN)
        
        # تحليلات زمنية
        last_30_days = timezone.now() - timedelta(days=30)
        
        # إنتاجية المحاصيل
        crop_analytics = CropAnalytics.objects.filter(
            crop__farm=farm,
            date__gte=last_30_days
        ).order_by('date')
        
        # بيانات IoT
        iot_analytics = IoTAnalytics.objects.filter(
            device__farm=farm,
            date__gte=last_30_days
        ).order_by('date')
        
        # التحليلات المالية
        financial_analytics = FinancialAnalytics.objects.filter(
            farm=farm,
            date__gte=last_30_days
        ).order_by('date')
        
        # التنبؤات
        prediction_service = PredictionService()
        yield_predictions = prediction_service.predict_crop_yield(farm)
        disease_risk = prediction_service.predict_disease_risk(farm)
        irrigation_needs = prediction_service.predict_irrigation_needs(farm)
        
        data = {
            'farm_info': {
                'id': farm.id,
                'name': farm.name,
                'type': farm.type,
                'area_hectares': float(farm.area_hectares),
                'status': farm.status,
                'location': {
                    'latitude': float(farm.location.y),
                    'longitude': float(farm.location.x)
                } if farm.location else None,
                'total_investment': float(farm.total_investment),
                'expected_revenue': float(farm.expected_annual_revenue),
                'water_efficiency': float(farm.water_efficiency),
                'productivity_index': float(farm.productivity_index),
                'sustainability_score': float(farm.sustainability_score),
            },
            'crop_analytics': CropAnalyticsSerializer(crop_analytics, many=True).data,
            'iot_analytics': IoTAnalyticsSerializer(iot_analytics, many=True).data,
            'financial_analytics': FinancialAnalyticsSerializer(financial_analytics, many=True).data,
            'predictions': {
                'yield_predictions': yield_predictions,
                'disease_risk': disease_risk,
                'irrigation_needs': irrigation_needs,
            },
            'recent_activities': self._get_recent_activities(farm),
            'upcoming_tasks': self._get_upcoming_tasks(farm),
        }
        
        return Response(data)
    
    def _get_recent_activities(self, farm):
        """الحصول على الأنشطة الحديثة"""
        recent_calendar = CropCalendar.objects.filter(
            crop__farm=farm,
            completed_date__isnull=False
        ).order_by('-completed_date')[:10]
        
        return [
            {
                'id': event.id,
                'title': event.title,
                'type': event.event_type,
                'completed_date': event.completed_date,
                'crop': event.crop.name,
            }
            for event in recent_calendar
        ]
    
    def _get_upcoming_tasks(self, farm):
        """الحصول على المهام القادمة"""
        upcoming_tasks = CropCalendar.objects.filter(
            crop__farm=farm,
            status='pending',
            scheduled_date__gte=timezone.now().date()
        ).order_by('scheduled_date')[:10]
        
        return [
            {
                'id': task.id,
                'title': task.title,
                'type': task.event_type,
                'scheduled_date': task.scheduled_date,
                'priority': task.priority,
                'crop': task.crop.name,
            }
            for task in upcoming_tasks
        ]
    
    @action(detail=False, methods=['get'])
    def performance_comparison(self, request):
        """مقارنة الأداء بين المزارع"""
        user = request.user
        farms = Farm.objects.filter(owner=user, is_active=True)
        
        comparison_data = []
        
        for farm in farms:
            # إحصائيات المحاصيل
            crop_stats = Crop.objects.filter(farm=farm).aggregate(
                total_yield=Sum('actual_yield'),
                avg_health=Avg('health_score'),
                total_revenue=Sum('actual_revenue')
            )
            
            # إحصائيات IoT
            iot_stats = SensorReading.objects.filter(
                device__farm=farm,
                timestamp__gte=timezone.now() - timedelta(days=30)
            ).aggregate(
                avg_temp=Avg('temperature'),
                avg_humidity=Avg('humidity'),
                avg_soil_moisture=Avg('soil_moisture')
            )
            
            comparison_data.append({
                'farm_id': farm.id,
                'farm_name': farm.name,
                'farm_type': farm.type,
                'area_hectares': float(farm.area_hectares),
                'water_efficiency': float(farm.water_efficiency),
                'productivity_index': float(farm.productivity_index),
                'sustainability_score': float(farm.sustainability_score),
                'total_yield': float(crop_stats['total_yield'] or 0),
                'avg_health_score': float(crop_stats['avg_health'] or 0),
                'total_revenue': float(crop_stats['total_revenue'] or 0),
                'avg_temperature': float(iot_stats['avg_temp'] or 0),
                'avg_humidity': float(iot_stats['avg_humidity'] or 0),
                'avg_soil_moisture': float(iot_stats['avg_soil_moisture'] or 0),
            })
        
        return Response(comparison_data)
    
    @action(detail=False, methods=['get'])
    def efficiency_trends(self, request):
        """اتجاهات الكفاءة عبر الزمن"""
        user = request.user
        days = int(request.query_params.get('days', 90))
        
        since_date = timezone.now() - timedelta(days=days)
        
        analytics = FarmAnalytics.objects.filter(
            farm__owner=user,
            date__gte=since_date,
            metric_type__in=['water_efficiency', 'energy_efficiency', 'productivity_index']
        ).order_by('date')
        
        # تجميع البيانات حسب التاريخ
        trends_data = {}
        
        for analytic in analytics:
            date_str = analytic.date.strftime('%Y-%m-%d')
            if date_str not in trends_data:
                trends_data[date_str] = {'date': date_str}
            
            trends_data[date_str][analytic.metric_type] = float(analytic.value)
        
        # تحويل إلى قائمة مرتبة
        trends_list = sorted(trends_data.values(), key=lambda x: x['date'])
        
        return Response(trends_list)


class CropAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet لتحليلات المحاصيل"""
    
    queryset = CropAnalytics.objects.all()
    serializer_class = CropAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['crop', 'date', 'metric_type']
    search_fields = ['crop__name', 'metric_type']
    ordering_fields = ['date', 'value', 'created_at']
    
    def get_queryset(self):
        return self.queryset.filter(crop__farm__owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def crop_performance(self, request):
        """أداء المحاصيل"""
        user = request.user
        
        # أداء المحاصيل حسب الفئة
        category_performance = Crop.objects.filter(
            farm__owner=user,
            status__in=['growing', 'harvesting', 'harvested']
        ).values('category').annotate(
            count=Count('id'),
            avg_health=Avg('health_score'),
            avg_yield=Avg('actual_yield'),
            total_revenue=Sum('actual_revenue'),
            total_cost=Sum('total_cost')
        )
        
        # أفضل المحاصيل أداءً
        best_crops = Crop.objects.filter(
            farm__owner=user,
            actual_yield__isnull=False
        ).order_by('-actual_yield')[:10]
        
        # أسوأ المحاصيل أداءً
        worst_crops = Crop.objects.filter(
            farm__owner=user,
            actual_yield__isnull=False
        ).order_by('actual_yield')[:10]
        
        data = {
            'category_performance': list(category_performance),
            'best_crops': [
                {
                    'id': crop.id,
                    'name': crop.name,
                    'category': crop.category,
                    'actual_yield': float(crop.actual_yield or 0),
                    'health_score': float(crop.health_score),
                    'revenue': float(crop.actual_revenue or 0),
                    'profit_margin': float((crop.actual_revenue or 0) - crop.total_cost),
                    'farm_name': crop.farm.name,
                }
                for crop in best_crops
            ],
            'worst_crops': [
                {
                    'id': crop.id,
                    'name': crop.name,
                    'category': crop.category,
                    'actual_yield': float(crop.actual_yield or 0),
                    'health_score': float(crop.health_score),
                    'revenue': float(crop.actual_revenue or 0),
                    'profit_margin': float((crop.actual_revenue or 0) - crop.total_cost),
                    'farm_name': crop.farm.name,
                }
                for crop in worst_crops
            ],
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def health_monitoring(self, request):
        """مراقبة صحة المحاصيل"""
        user = request.user
        
        # المحاصيل المصابة
        diseased_crops = Crop.objects.filter(
            farm__owner=user,
            status='diseased'
        ).select_related('farm')
        
        # المحاصيل عالية الخطورة
        high_risk_crops = Crop.objects.filter(
            farm__owner=user,
            disease_risk__gt=70
        ).select_related('farm')
        
        # متوسط درجات الصحة
        health_stats = Crop.objects.filter(
            farm__owner=user
        ).aggregate(
            avg_health=Avg('health_score'),
            min_health=Min('health_score'),
            max_health=Max('health_score')
        )
        
        data = {
            'diseased_crops': [
                {
                    'id': crop.id,
                    'name': crop.name,
                    'farm_name': crop.farm.name,
                    'health_score': float(crop.health_score),
                    'disease_risk': float(crop.disease_risk),
                    'status': crop.status,
                }
                for crop in diseased_crops[:20]
            ],
            'high_risk_crops': [
                {
                    'id': crop.id,
                    'name': crop.name,
                    'farm_name': crop.farm.name,
                    'health_score': float(crop.health_score),
                    'disease_risk': float(crop.disease_risk),
                    'status': crop.status,
                }
                for crop in high_risk_crops[:20]
            ],
            'health_statistics': {
                'average_health': float(health_stats['avg_health'] or 0),
                'minimum_health': float(health_stats['min_health'] or 0),
                'maximum_health': float(health_stats['max_health'] or 0),
            },
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def yield_predictions(self, request):
        """تنبؤات الإنتاجية"""
        user = request.user
        
        prediction_service = PredictionService()
        
        # التنبؤات للمحاصيل الحالية
        current_crops = Crop.objects.filter(
            farm__owner=user,
            status__in=['growing', 'flowering', 'fruiting'],
            expected_harvest_date__gte=timezone.now().date()
        )
        
        predictions = []
        
        for crop in current_crops:
            prediction = prediction_service.predict_single_crop_yield(crop)
            predictions.append({
                'crop_id': crop.id,
                'crop_name': crop.name,
                'farm_name': crop.farm.name,
                'current_stage': crop.status,
                'predicted_yield': prediction.get('predicted_yield', 0),
                'confidence_level': prediction.get('confidence', 0),
                'expected_harvest_date': crop.expected_harvest_date,
                'risk_factors': prediction.get('risk_factors', []),
                'recommendations': prediction.get('recommendations', []),
            })
        
        return Response(predictions)


class IoTAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet لتحليلات IoT"""
    
    queryset = IoTAnalytics.objects.all()
    serializer_class = IoTAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['device', 'date', 'metric_type']
    search_fields = ['device__name', 'metric_type']
    ordering_fields = ['date', 'value', 'created_at']
    
    def get_queryset(self):
        return self.queryset.filter(device__farm__owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def sensor_dashboard(self, request):
        """لوحة معلومات المستشعرات"""
        user = request.user
        hours = int(request.query_params.get('hours', 24))
        
        since = timezone.now() - timedelta(hours=hours)
        
        # أحدث القراءات
        latest_readings = SensorReading.objects.filter(
            device__farm__owner=user,
            timestamp__gte=since
        ).select_related('device').order_by('-timestamp')[:100]
        
        # متوسط القراءات حسب الجهاز
        device_averages = SensorReading.objects.filter(
            device__farm__owner=user,
            timestamp__gte=since
        ).values('device__name', 'device__id').annotate(
            avg_temp=Avg('temperature'),
            avg_humidity=Avg('humidity'),
            avg_soil_moisture=Avg('soil_moisture'),
            avg_ph=Avg('ph'),
            avg_light=Avg('light_intensity'),
            reading_count=Count('id')
        )
        
        # أجهزة غير نشطة
        inactive_devices = IoTDevice.objects.filter(
            farm__owner=user,
            status='offline'
        ).select_related('farm')
        
        # أجهزة تحتاج صيانة
        maintenance_devices = IoTDevice.objects.filter(
            farm__owner=user,
            next_maintenance_date__lte=timezone.now().date()
        ).select_related('farm')
        
        data = {
            'latest_readings': [
                {
                    'id': reading.id,
                    'device_name': reading.device.name,
                    'device_type': reading.device.device_type,
                    'farm_name': reading.device.farm.name,
                    'timestamp': reading.timestamp,
                    'temperature': float(reading.temperature) if reading.temperature else None,
                    'humidity': float(reading.humidity) if reading.humidity else None,
                    'soil_moisture': float(reading.soil_moisture) if reading.soil_moisture else None,
                    'ph': float(reading.ph) if reading.ph else None,
                    'light_intensity': float(reading.light_intensity) if reading.light_intensity else None,
                    'data_quality': reading.data_quality,
                }
                for reading in latest_readings
            ],
            'device_averages': [
                {
                    'device_id': avg['device__id'],
                    'device_name': avg['device__name'],
                    'avg_temperature': float(avg['avg_temp']) if avg['avg_temp'] else None,
                    'avg_humidity': float(avg['avg_humidity']) if avg['avg_humidity'] else None,
                    'avg_soil_moisture': float(avg['avg_soil_moisture']) if avg['avg_soil_moisture'] else None,
                    'avg_ph': float(avg['avg_ph']) if avg['avg_ph'] else None,
                    'avg_light_intensity': float(avg['avg_light']) if avg['avg_light'] else None,
                    'reading_count': avg['reading_count'],
                }
                for avg in device_averages
            ],
            'inactive_devices': [
                {
                    'id': device.id,
                    'name': device.name,
                    'type': device.device_type,
                    'farm_name': device.farm.name,
                    'last_activity': device.created_at,
                    'battery_level': float(device.battery_level) if device.battery_level else None,
                }
                for device in inactive_devices
            ],
            'maintenance_devices': [
                {
                    'id': device.id,
                    'name': device.name,
                    'type': device.device_type,
                    'farm_name': device.farm.name,
                    'next_maintenance_date': device.next_maintenance_date,
                    'last_maintenance_date': device.last_maintenance_date,
                }
                for device in maintenance_devices
            ],
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def environmental_trends(self, request):
        """اتجاهات البيئة"""
        user = request.user
        days = int(request.query_params.get('days', 30))
        
        since = timezone.now() - timedelta(days=days)
        
        # متوسط القراءات اليومية
        daily_averages = SensorReading.objects.filter(
            device__farm__owner=user,
            timestamp__gte=since
        ).annotate(
            date=TruncDate('timestamp')
        ).values('date').annotate(
            avg_temp=Avg('temperature'),
            avg_humidity=Avg('humidity'),
            avg_soil_moisture=Avg('soil_moisture'),
            avg_ph=Avg('ph'),
            avg_light=Avg('light_intensity'),
            avg_co2=Avg('co2'),
        ).order_by('date')
        
        # القراءات الشاذة
        outliers = []
        readings = SensorReading.objects.filter(
            device__farm__owner=user,
            timestamp__gte=since
        )
        
        for reading in readings[:1000]:  # تحديد لأفضل الأداء
            if reading.is_outlier('temperature'):
                outliers.append({
                    'type': 'temperature_outlier',
                    'device': reading.device.name,
                    'value': float(reading.temperature),
                    'timestamp': reading.timestamp,
                })
        
        data = {
            'daily_averages': [
                {
                    'date': avg['date'].strftime('%Y-%m-%d'),
                    'avg_temperature': float(avg['avg_temp']) if avg['avg_temp'] else None,
                    'avg_humidity': float(avg['avg_humidity']) if avg['avg_humidity'] else None,
                    'avg_soil_moisture': float(avg['avg_soil_moisture']) if avg['avg_soil_moisture'] else None,
                    'avg_ph': float(avg['avg_ph']) if avg['avg_ph'] else None,
                    'avg_light_intensity': float(avg['avg_light']) if avg['avg_light'] else None,
                    'avg_co2': float(avg['avg_co2']) if avg['avg_co2'] else None,
                }
                for avg in daily_averages
            ],
            'outliers': outliers,
        }
        
        return Response(data)


class FinancialAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet للتحليلات المالية"""
    
    queryset = FinancialAnalytics.objects.all()
    serializer_class = FinancialAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['farm', 'date', 'metric_type']
    search_fields = ['farm__name', 'metric_type']
    ordering_fields = ['date', 'value', 'created_at']
    
    def get_queryset(self):
        return self.queryset.filter(farm__owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def financial_dashboard(self, request):
        """لوحة المعلومات المالية"""
        user = request.user
        
        # الإيرادات والتكاليف
        current_month = timezone.now().replace(day=1)
        
        # إيرادات الشهر الحالي
        monthly_revenue = Crop.objects.filter(
            farm__owner=user,
            actual_harvest_date__month=current_month.month,
            actual_harvest_date__year=current_month.year,
            actual_revenue__isnull=False
        ).aggregate(total=Sum('actual_revenue'))['total'] or 0
        
        # تكاليف الشهر الحالي
        monthly_costs = Crop.objects.filter(
            farm__owner=user,
            created_at__month=current_month.month,
            created_at__year=current_month.year
        ).aggregate(total=Sum('total_cost'))['total'] or 0
        
        # معاملات السوق
        marketplace_transactions = Transaction.objects.filter(
            buyer=user,
            created_at__month=current_month.month,
            created_at__year=current_month.year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # ROI للمزارع
        farm_roi = []
        farms = Farm.objects.filter(owner=user, is_active=True)
        
        for farm in farms:
            total_investment = farm.total_investment
            total_revenue = Crop.objects.filter(
                farm=farm,
                actual_revenue__isnull=False
            ).aggregate(total=Sum('actual_revenue'))['total'] or 0
            
            roi = ((total_revenue - total_investment) / total_investment * 100) if total_investment > 0 else 0
            
            farm_roi.append({
                'farm_id': farm.id,
                'farm_name': farm.name,
                'total_investment': float(total_investment),
                'total_revenue': float(total_revenue),
                'roi_percentage': float(roi),
            })
        
        data = {
            'monthly_summary': {
                'revenue': float(monthly_revenue),
                'costs': float(monthly_costs),
                'profit': float(monthly_revenue - monthly_costs),
                'marketplace_spending': float(marketplace_transactions),
            },
            'farm_roi': farm_roi,
            'top_profit_crops': self._get_top_profit_crops(user),
            'cost_breakdown': self._get_cost_breakdown(user),
        }
        
        return Response(data)
    
    def _get_top_profit_crops(self, user):
        """أفضل المحاصيل ربحية"""
        crops = Crop.objects.filter(
            farm__owner=user,
            actual_revenue__isnull=False
        ).order_by('-actual_revenue')[:10]
        
        return [
            {
                'id': crop.id,
                'name': crop.name,
                'farm_name': crop.farm.name,
                'revenue': float(crop.actual_revenue or 0),
                'cost': float(crop.total_cost),
                'profit': float((crop.actual_revenue or 0) - crop.total_cost),
                'profit_margin': float(((crop.actual_revenue or 0) - crop.total_cost) / crop.total_cost * 100) if crop.total_cost > 0 else 0,
            }
            for crop in crops
        ]
    
    def _get_cost_breakdown(self, user):
        """تحليل التكاليف"""
        cost_summary = Crop.objects.filter(
            farm__owner=user
        ).aggregate(
            total_seed_cost=Sum('seed_cost'),
            total_fertilizer_cost=Sum('fertilizer_cost'),
            total_pesticide_cost=Sum('pesticide_cost'),
            total_labor_cost=Sum('labor_cost'),
        )
        
        return {
            'seeds': float(cost_summary['total_seed_cost'] or 0),
            'fertilizers': float(cost_summary['total_fertilizer_cost'] or 0),
            'pesticides': float(cost_summary['total_pesticide_cost'] or 0),
            'labor': float(cost_summary['total_labor_cost'] or 0),
        }


class WeatherAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet لتحليلات الطقس"""
    
    queryset = WeatherAnalytics.objects.all()
    serializer_class = WeatherAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['farm', 'date', 'metric_type']
    search_fields = ['farm__name', 'metric_type']
    ordering_fields = ['date', 'value', 'created_at']
    
    def get_queryset(self):
        return self.queryset.filter(farm__owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def weather_alerts(self, request):
        """تنبيهات الطقس"""
        user = request.user
        
        # الحصول على بيانات الطقس الحالية
        farms = Farm.objects.filter(owner=user, is_active=True)
        
        alerts = []
        
        for farm in farms:
            if farm.location:
                from apps.weather.services import WeatherService
                weather_service = WeatherService()
                
                current_weather = weather_service.get_current_weather(
                    latitude=farm.location.y,
                    longitude=farm.location.x
                )
                
                forecast = weather_service.get_forecast(
                    latitude=farm.location.y,
                    longitude=farm.location.x,
                    days=5
                )
                
                # تحليل التنبيهات
                if current_weather:
                    alerts.extend(self._analyze_weather_alerts(farm, current_weather, forecast))
        
        return Response(alerts)
    
    def _analyze_weather_alerts(self, farm, current_weather, forecast):
        """تحليل تنبيهات الطقس"""
        alerts = []
        
        # تنبيهات درجة الحرارة
        if current_weather.get('temperature'):
            temp = current_weather['temperature']
            if temp > 40:
                alerts.append({
                    'type': 'extreme_heat',
                    'severity': 'high',
                    'farm_id': farm.id,
                    'farm_name': farm.name,
                    'message': f'تحذير: درجة حرارة عالية جداً ({temp}°C)',
                    'recommendation': 'زيادة الري، توفير الظل للمحاصيل الحساسة',
                    'timestamp': timezone.now(),
                })
            elif temp < 5:
                alerts.append({
                    'type': 'frost_risk',
                    'severity': 'high',
                    'farm_id': farm.id,
                    'farm_name': farm.name,
                    'message': f'تحذير: خطر الصقيع ({temp}°C)',
                    'recommendation': 'تغطية المحاصيل الحساسة، تفعيل أنظمة التدفئة',
                    'timestamp': timezone.now(),
                })
        
        # تنبيهات الأمطار
        if forecast:
            for day in forecast[:3]:  # أول 3 أيام
                if day.get('rain', 0) > 20:
                    alerts.append({
                        'type': 'heavy_rain',
                        'severity': 'medium',
                        'farm_id': farm.id,
                        'farm_name': farm.name,
                        'message': f'تحذير: أمطار غزيرة متوقعة ({day["rain"]}mm)',
                        'recommendation': 'تقليل الري، تصريف المياه الزائدة',
                        'date': day.get('date'),
                    })
        
        return alerts


class MarketAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet لتحليلات السوق"""
    
    queryset = MarketAnalytics.objects.all()
    serializer_class = MarketAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['crop_category', 'date', 'metric_type']
    search_fields = ['crop_category', 'metric_type']
    ordering_fields = ['date', 'value', 'created_at']
    
    def get_queryset(self):
        return self.queryset.filter(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def market_overview(self, request):
        """نظرة عامة على السوق"""
        
        # الأسعار الحالية
        current_listings = CropListing.objects.filter(
            status='active',
            created_at__gte=timezone.now() - timedelta(days=7)
        ).select_related('crop').order_by('-created_at')
        
        # المتوسطات السعرية حسب الفئة
        price_by_category = current_listings.values('crop__category').annotate(
            avg_price=Avg('price_per_unit'),
            min_price=Min('price_per_unit'),
            max_price=Max('price_per_unit'),
            listing_count=Count('id')
        )
        
        # أكثر المحاصيل طلباً
        most_demanded = current_listings.values('crop__name', 'crop__category').annotate(
            demand_count=Count('id'),
            avg_price=Avg('price_per_unit')
        ).order_by('-demand_count')[:10]
        
        # المعاملات الأخيرة
        recent_transactions = Transaction.objects.filter(
            status='completed'
        ).select_related('listing__crop').order_by('-created_at')[:20]
        
        data = {
            'price_by_category': list(price_by_category),
            'most_demanded_crops': list(most_demanded),
            'recent_transactions': [
                {
                    'id': trans.id,
                    'crop_name': trans.listing.crop.name,
                    'category': trans.listing.crop.category,
                    'price': float(trans.amount),
                    'quantity': float(trans.quantity),
                    'buyer': trans.buyer.username,
                    'seller': trans.listing.seller.username,
                    'date': trans.created_at,
                }
                for trans in recent_transactions
            ],
            'market_summary': {
                'total_active_listings': current_listings.count(),
                'total_categories': len(set(current_listings.values_list('crop__category', flat=True))),
                'price_volatility': self._calculate_price_volatility(),
            }
        }
        
        return Response(data)
    
    def _calculate_price_volatility(self):
        """حساب تقلبات الأسعار"""
        # حساب معياري الانحراف للأسعار في آخر 30 يوماً
        recent_prices = CropListing.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30),
            price_per_unit__isnull=False
        ).values_list('price_per_unit', flat=True)
        
        if len(recent_prices) < 10:
            return 0
        
        mean_price = sum(recent_prices) / len(recent_prices)
        variance = sum((price - mean_price) ** 2 for price in recent_prices) / len(recent_prices)
        volatility = (variance ** 0.5) / mean_price * 100
        
        return float(volatility)