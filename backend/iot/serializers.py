from rest_framework import serializers
from .models import IoTDevice, Sensor, Actuator, SensorReading

class SensorReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorReading
        fields = '__all__'
        read_only_fields = ('id', 'timestamp')


class SensorSerializer(serializers.ModelSerializer):
    latest_reading = serializers.SerializerMethodField()
    
    class Meta:
        model = Sensor
        fields = ('id', 'device', 'sensor_type', 'unit', 'min_value', 
                  'max_value', 'threshold_low', 'threshold_high', 
                  'latest_reading', 'created_at')
        read_only_fields = ('id', 'created_at')
    
    def get_latest_reading(self, obj):
        latest = obj.readings.order_by('-timestamp').first()
        if latest:
            return SensorReadingSerializer(latest).data
        return None


class ActuatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actuator
        fields = ('id', 'device', 'actuator_type', 'status', 
                  'last_activated', 'created_at')
        read_only_fields = ('id', 'created_at', 'last_activated')


class IoTDeviceSerializer(serializers.ModelSerializer):
    field_name = serializers.CharField(source='field.name', read_only=True)
    sensors_count = serializers.SerializerMethodField()
    actuators_count = serializers.SerializerMethodField()
    
    class Meta:
        model = IoTDevice
        fields = ('id', 'field', 'field_name', 'device_id', 'name', 
                  'device_type', 'status', 'battery_level', 'signal_strength', 
                  'latitude', 'longitude', 'last_seen', 'sensors_count', 
                  'actuators_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'last_seen')
    
    def get_sensors_count(self, obj):
        return obj.sensors.count()
    
    def get_actuators_count(self, obj):
        return obj.actuators.count()


class IoTDeviceDetailSerializer(IoTDeviceSerializer):
    sensors = SensorSerializer(many=True, read_only=True)
    actuators = ActuatorSerializer(many=True, read_only=True)
    
    class Meta(IoTDeviceSerializer.Meta):
        fields = IoTDeviceSerializer.Meta.fields + ('sensors', 'actuators')
