import 'package:json_annotation/json_annotation.dart';

part 'iot_device.g.dart';

@JsonSerializable()
class IoTDevice {
  final int id;
  final int field;
  @JsonKey(name: 'field_name')
  final String? fieldName;
  @JsonKey(name: 'device_id')
  final String deviceId;
  final String name;
  @JsonKey(name: 'device_type')
  final String deviceType;
  final String status;
  @JsonKey(name: 'battery_level')
  final int? batteryLevel;
  @JsonKey(name: 'signal_strength')
  final int? signalStrength;
  final double? latitude;
  final double? longitude;
  @JsonKey(name: 'last_seen')
  final DateTime? lastSeen;
  @JsonKey(name: 'sensors_count')
  final int? sensorsCount;
  @JsonKey(name: 'actuators_count')
  final int? actuatorsCount;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  @JsonKey(name: 'updated_at')
  final DateTime updatedAt;

  IoTDevice({
    required this.id,
    required this.field,
    this.fieldName,
    required this.deviceId,
    required this.name,
    required this.deviceType,
    required this.status,
    this.batteryLevel,
    this.signalStrength,
    this.latitude,
    this.longitude,
    this.lastSeen,
    this.sensorsCount,
    this.actuatorsCount,
    required this.createdAt,
    required this.updatedAt,
  });

  factory IoTDevice.fromJson(Map<String, dynamic> json) =>
      _$IoTDeviceFromJson(json);
  Map<String, dynamic> toJson() => _$IoTDeviceToJson(this);
}

@JsonSerializable()
class Sensor {
  final int id;
  final int device;
  @JsonKey(name: 'sensor_type')
  final String sensorType;
  final String unit;
  @JsonKey(name: 'min_value')
  final double? minValue;
  @JsonKey(name: 'max_value')
  final double? maxValue;
  @JsonKey(name: 'threshold_low')
  final double? thresholdLow;
  @JsonKey(name: 'threshold_high')
  final double? thresholdHigh;
  @JsonKey(name: 'latest_reading')
  final SensorReading? latestReading;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;

  Sensor({
    required this.id,
    required this.device,
    required this.sensorType,
    required this.unit,
    this.minValue,
    this.maxValue,
    this.thresholdLow,
    this.thresholdHigh,
    this.latestReading,
    required this.createdAt,
  });

  factory Sensor.fromJson(Map<String, dynamic> json) => _$SensorFromJson(json);
  Map<String, dynamic> toJson() => _$SensorToJson(this);
}

@JsonSerializable()
class SensorReading {
  final int id;
  final int sensor;
  final double value;
  final DateTime timestamp;

  SensorReading({
    required this.id,
    required this.sensor,
    required this.value,
    required this.timestamp,
  });

  factory SensorReading.fromJson(Map<String, dynamic> json) =>
      _$SensorReadingFromJson(json);
  Map<String, dynamic> toJson() => _$SensorReadingToJson(this);
}

@JsonSerializable()
class Actuator {
  final int id;
  final int device;
  @JsonKey(name: 'actuator_type')
  final String actuatorType;
  final String status;
  @JsonKey(name: 'last_activated')
  final DateTime? lastActivated;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;

  Actuator({
    required this.id,
    required this.device,
    required this.actuatorType,
    required this.status,
    this.lastActivated,
    required this.createdAt,
  });

  factory Actuator.fromJson(Map<String, dynamic> json) =>
      _$ActuatorFromJson(json);
  Map<String, dynamic> toJson() => _$ActuatorToJson(this);
}
