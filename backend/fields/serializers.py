"""
Serializers for fields app.
"""

from rest_framework import serializers
from .models import Field


class FieldSerializer(serializers.ModelSerializer):
    """
    Serializer for Field model.
    """

    class Meta:
        model = Field
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


