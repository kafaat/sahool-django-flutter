"""
Admin configuration for iot app.
"""

from django.contrib import admin
from .models import IoTDevice, SensorReading


@admin.register(IoTDevice)
class IoTDeviceAdmin(admin.ModelAdmin):
    list_display = ['id', 'field', 'device_id', 'device_type']
    search_fields = ['id']
    list_filter = ['created_at']


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ['id', 'device', 'temperature', 'humidity']
    search_fields = ['id']
    list_filter = ['timestamp']
