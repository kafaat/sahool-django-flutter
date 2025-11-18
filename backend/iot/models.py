from django.db import models
from fields.models import Field

class IoTDevice(models.Model):
    """نموذج جهاز IoT"""
    
    DEVICE_TYPES = (
        ('soil_moisture', 'مستشعر رطوبة التربة'),
        ('temperature', 'مستشعر درجة الحرارة'),
        ('humidity', 'مستشعر الرطوبة'),
        ('water_valve', 'صمام مياه'),
        ('pump', 'مضخة'),
        ('weather_station', 'محطة طقس'),
    )
    
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=100, unique=True)
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPES)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default='active')
    battery_level = models.IntegerField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    installed_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'جهاز IoT'
        verbose_name_plural = 'أجهزة IoT'
    
    def __str__(self):
        return f"{self.name} ({self.device_id})"


class SensorReading(models.Model):
    """قراءات المستشعرات"""
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='readings')
    timestamp = models.DateTimeField(auto_now_add=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    
    class Meta:
        verbose_name = 'قراءة مستشعر'
        verbose_name_plural = 'قراءات المستشعرات'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - {self.value} {self.unit}"


class Alert(models.Model):
    """التنبيهات"""
    
    SEVERITY_LEVELS = (
        ('info', 'معلومة'),
        ('warning', 'تحذير'),
        ('critical', 'حرج'),
    )
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'تنبيه'
        verbose_name_plural = 'التنبيهات'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
