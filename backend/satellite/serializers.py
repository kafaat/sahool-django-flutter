"""
Serializers for satellite app.
"""

from rest_framework import serializers
from .models import SatelliteImage


class SatelliteImageSerializer(serializers.ModelSerializer):
    """
    Serializer for SatelliteImage model.
    """

    class Meta:
        model = SatelliteImage
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


