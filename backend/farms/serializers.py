"""
Serializers for farms app.
"""

from rest_framework import serializers
from .models import Farm


class FarmSerializer(serializers.ModelSerializer):
    """
    Serializer for Farm model.
    """

    class Meta:
        model = Farm
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


