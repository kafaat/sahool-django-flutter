"""
نظام التقارير للمزارع
"""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Min, Max, Q
from .models import Farm
from fields.models import Field, IrrigationSchedule
from iot.models import Sensor, SensorReading


class FarmReportGenerator:
    """مولد التقارير للمزارع"""
    
    def __init__(self, farm: Farm):
        self.farm = farm
    
    def get_monthly_report(self, months=1):
        """
        إنشاء تقرير شهري للمزرعة
        
        Args:
            months: عدد الأشهر للتقرير (افتراضي: 1)
            
        Returns:
            dict: التقرير الشامل
        """
        start_date = timezone.now() - timedelta(days=30 * months)
        
        report = {
            'farm': {
                'id': self.farm.id,
                'name': self.farm.name,
                'location': self.farm.location,
                'total_area': float(self.farm.total_area) if self.farm.total_area else 0,
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': timezone.now().isoformat(),
                'months': months,
            },
            'fields': self._get_fields_stats(start_date),
            'irrigation': self._get_irrigation_stats(start_date),
            'sensors': self._get_sensor_stats(start_date),
            'crops': self._get_crops_stats(),
            'devices': self._get_devices_stats(),
        }
        
        return report
    
    def _get_fields_stats(self, start_date):
        """إحصائيات الحقول"""
        fields = Field.objects.filter(farm=self.farm)
        
        return {
            'total_count': fields.count(),
            'total_area': float(fields.aggregate(
                total=Sum('area')
            )['total'] or 0),
            'by_soil_type': dict(
                fields.values('soil_type').annotate(
                    count=Count('id')
                ).values_list('soil_type', 'count')
            ),
            'active_fields': fields.filter(
                is_active=True
            ).count(),
        }
    
    def _get_irrigation_stats(self, start_date):
        """إحصائيات الري"""
        schedules = IrrigationSchedule.objects.filter(
            field__farm=self.farm,
            created_at__gte=start_date
        )
        
        return {
            'total_schedules': schedules.count(),
            'completed_schedules': schedules.filter(
                status='completed'
            ).count(),
            'total_water_used': float(schedules.filter(
                status='completed'
            ).aggregate(
                total=Sum('water_amount')
            )['total'] or 0),
            'avg_water_per_schedule': float(schedules.filter(
                status='completed'
            ).aggregate(
                avg=Avg('water_amount')
            )['avg'] or 0),
            'by_method': dict(
                schedules.values('method').annotate(
                    count=Count('id')
                ).values_list('method', 'count')
            ),
        }
    
    def _get_sensor_stats(self, start_date):
        """إحصائيات المستشعرات"""
        sensors = Sensor.objects.filter(
            device__field__farm=self.farm
        )
        
        readings = SensorReading.objects.filter(
            sensor__in=sensors,
            timestamp__gte=start_date
        )
        
        stats = {
            'total_sensors': sensors.count(),
            'total_readings': readings.count(),
            'by_type': {},
        }
        
        # إحصائيات حسب نوع المستشعر
        for sensor_type in ['temperature', 'humidity', 'soil_moisture', 'ph']:
            type_readings = readings.filter(sensor__sensor_type=sensor_type)
            
            if type_readings.exists():
                stats['by_type'][sensor_type] = {
                    'count': type_readings.count(),
                    'avg': float(type_readings.aggregate(
                        avg=Avg('value')
                    )['avg'] or 0),
                    'min': float(type_readings.aggregate(
                        min=Min('value')
                    )['min'] or 0),
                    'max': float(type_readings.aggregate(
                        max=Max('value')
                    )['max'] or 0),
                }
        
        return stats
    
    def _get_crops_stats(self):
        """إحصائيات المحاصيل"""
        from .models import Crop
        
        crops = Crop.objects.filter(farm=self.farm)
        
        return {
            'total_count': crops.count(),
            'by_type': dict(
                crops.values('crop_type').annotate(
                    count=Count('id')
                ).values_list('crop_type', 'count')
            ),
            'active_crops': crops.filter(
                is_active=True
            ).count(),
        }
    
    def _get_devices_stats(self):
        """إحصائيات الأجهزة"""
        from iot.models import IoTDevice
        
        devices = IoTDevice.objects.filter(field__farm=self.farm)
        
        return {
            'total_count': devices.count(),
            'active_devices': devices.filter(
                is_active=True
            ).count(),
            'by_type': dict(
                devices.values('device_type').annotate(
                    count=Count('id')
                ).values_list('device_type', 'count')
            ),
            'online_devices': devices.filter(
                status='online'
            ).count(),
        }


def generate_farm_report(farm_id, months=1):
    """
    دالة مساعدة لإنشاء تقرير المزرعة
    
    Args:
        farm_id: معرف المزرعة
        months: عدد الأشهر
        
    Returns:
        dict: التقرير
    """
    try:
        farm = Farm.objects.get(id=farm_id)
        generator = FarmReportGenerator(farm)
        return generator.get_monthly_report(months)
    except Farm.DoesNotExist:
        return {'error': 'Farm not found'}
