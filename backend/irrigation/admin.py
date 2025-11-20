"""
Admin configuration for irrigation app.
"""

from django.contrib import admin
from .models import IrrigationSchedule


@admin.register(IrrigationSchedule)
class IrrigationScheduleAdmin(admin.ModelAdmin):
    list_display = ['id', 'field', 'start_time', 'duration_minutes']
    search_fields = ['id']
    list_filter = ['created_at']


