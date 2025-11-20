"""
Admin configuration for crops app.
"""

from django.contrib import admin
from .models import Crop


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ['id', 'field', 'name', 'variety']
    search_fields = ['id']
    list_filter = ['created_at']


