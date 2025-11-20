"""
Serializers for irrigation app.
"""

from rest_framework import serializers
from .models import IrrigationSchedule


class IrrigationScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for IrrigationSchedule model.
    """

    class Meta:
        model = IrrigationSchedule
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


