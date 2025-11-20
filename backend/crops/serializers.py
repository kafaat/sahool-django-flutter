"""
Serializers for crops app.
"""

from rest_framework import serializers
from .models import Crop


class CropSerializer(serializers.ModelSerializer):
    """
    Serializer for Crop model.
    """

    class Meta:
        model = Crop
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


