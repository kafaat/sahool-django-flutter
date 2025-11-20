"""
Admin configuration for fields app.
"""

from django.contrib import admin
from .models import Field


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ['id', 'farm', 'name', 'area']
    search_fields = ['id']
    list_filter = ['created_at']


