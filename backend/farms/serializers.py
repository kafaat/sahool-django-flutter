from rest_framework import serializers
from .models import Farm, Crop

class CropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = '__all__'


class FarmSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    fields_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Farm
        fields = ('id', 'owner', 'owner_name', 'name', 'location', 
                  'latitude', 'longitude', 'total_area', 'description', 
                  'image', 'fields_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_fields_count(self, obj):
        return obj.fields.count()


class FarmDetailSerializer(FarmSerializer):
    fields = serializers.SerializerMethodField()
    
    class Meta(FarmSerializer.Meta):
        fields = FarmSerializer.Meta.fields + ('fields',)
    
    def get_fields(self, obj):
        from fields.serializers import FieldSerializer
        return FieldSerializer(obj.fields.all(), many=True).data
