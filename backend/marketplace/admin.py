"""
Admin configuration for marketplace app.
"""

from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'seller', 'name', 'description']
    search_fields = ['id']
    list_filter = ['created_at']


