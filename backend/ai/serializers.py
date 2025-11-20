"""
Serializers for ai app.
"""

from rest_framework import serializers
from .models import DiseaseDetection


class DiseaseDetectionSerializer(serializers.ModelSerializer):
    """
    Serializer for DiseaseDetection model.
    """

    class Meta:
        model = DiseaseDetection
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


