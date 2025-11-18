from rest_framework import serializers
from .models import Field, IrrigationSchedule

class IrrigationScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = IrrigationSchedule
        fields = '__all__'
        read_only_fields = ('id', 'completed_at')


class FieldSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    crop_name = serializers.CharField(source='crop.name', read_only=True)
    devices_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Field
        fields = ('id', 'farm', 'farm_name', 'name', 'area', 'soil_type', 
                  'crop', 'crop_name', 'planting_date', 'expected_harvest_date', 
                  'status', 'notes', 'devices_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_devices_count(self, obj):
        return obj.devices.count()


class FieldDetailSerializer(FieldSerializer):
    irrigation_schedules = IrrigationScheduleSerializer(many=True, read_only=True)
    devices = serializers.SerializerMethodField()
    
    class Meta(FieldSerializer.Meta):
        fields = FieldSerializer.Meta.fields + ('irrigation_schedules', 'devices')
    
    def get_devices(self, obj):
        from iot.serializers import IoTDeviceSerializer
        return IoTDeviceSerializer(obj.devices.all(), many=True).data
