"""
Admin configuration for ai app.
"""

from django.contrib import admin
from .models import DiseaseDetection


@admin.register(DiseaseDetection)
class DiseaseDetectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'crop', 'image', 'disease_name']
    search_fields = ['id']
    list_filter = ['detected_at']


