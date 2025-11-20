"""
Admin configuration for weather app.
"""

from django.contrib import admin
from .models import WeatherData


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'farm', 'date', 'temperature_max']
    search_fields = ['id']
    list_filter = ['created_at']


