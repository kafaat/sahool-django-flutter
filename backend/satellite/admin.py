"""
Admin configuration for satellite app.
"""

from django.contrib import admin
from .models import SatelliteImage


@admin.register(SatelliteImage)
class SatelliteImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'field', 'image_date', 'ndvi_value']
    search_fields = ['id']
    list_filter = ['created_at']


