"""
Admin configuration for analytics app.
"""

from django.contrib import admin
from .models import FarmAnalytics


@admin.register(FarmAnalytics)
class FarmAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['id', 'farm', 'date', 'total_yield']
    search_fields = ['id']
    list_filter = ['created_at']


