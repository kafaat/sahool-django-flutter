"""
Serializers for weather app.
"""

from rest_framework import serializers
from .models import WeatherData


class WeatherDataSerializer(serializers.ModelSerializer):
    """
    Serializer for WeatherData model.
    """

    class Meta:
        model = WeatherData
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


