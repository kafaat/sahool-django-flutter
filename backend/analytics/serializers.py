"""
Serializers for analytics app.
"""

from rest_framework import serializers
from .models import FarmAnalytics


class FarmAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for FarmAnalytics model.
    """

    class Meta:
        model = FarmAnalytics
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


