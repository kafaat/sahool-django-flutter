"""
Admin configuration for farms app.
"""

from django.contrib import admin
from .models import Farm


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ['id', 'owner', 'name', 'location']
    search_fields = ['id']
    list_filter = ['created_at']


