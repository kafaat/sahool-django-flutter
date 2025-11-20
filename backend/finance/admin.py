"""
Admin configuration for finance app.
"""

from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'farm', 'transaction_type']
    search_fields = ['id']
    list_filter = ['created_at']


