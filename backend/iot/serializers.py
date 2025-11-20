"""
Serializers for iot app.
"""

from rest_framework import serializers
from .models import IoTDevice, SensorReading


class IoTDeviceSerializer(serializers.ModelSerializer):
    """
    Serializer for IoTDevice model.
    """

    class Meta:
        model = IoTDevice
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class SensorReadingSerializer(serializers.ModelSerializer):
    """
    Serializer for SensorReading model.
    """

    class Meta:
        model = SensorReading
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


