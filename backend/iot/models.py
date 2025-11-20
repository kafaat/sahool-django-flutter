"""
Models for iot app.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class IoTDevice(models.Model):
    """
    IoTDevice model.
    """

    field = models.ForeignKey('fields.Field', on_delete=models.CASCADE, related_name='iot_devices', verbose_name=_('الحقل'))
    device_id = models.CharField(max_length=100, unique=True, verbose_name=_('معرف الجهاز'))
    device_type = models.CharField(max_length=50, verbose_name=_('نوع الجهاز'))
    status = models.CharField(max_length=20, default='active', verbose_name=_('الحالة'))
    last_reading = models.DateTimeField(null=True, blank=True, verbose_name=_('آخر قراءة'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التحديث'))

    class Meta:
        verbose_name = _('IoTDevice')
        verbose_name_plural = _('IoTDevices')
        ordering = ['-created_at']

    def __str__(self):
        return f"{IoTDevice} {self.pk}"


class SensorReading(models.Model):
    """
    SensorReading model.
    """

    device = models.ForeignKey('IoTDevice', on_delete=models.CASCADE, related_name='readings', verbose_name=_('الجهاز'))
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_('درجة الحرارة'))
    humidity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_('الرطوبة'))
    soil_moisture = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_('رطوبة التربة'))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_('الوقت'))

    class Meta:
        verbose_name = _('SensorReading')
        verbose_name_plural = _('SensorReadings')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{SensorReading} {self.pk}"


