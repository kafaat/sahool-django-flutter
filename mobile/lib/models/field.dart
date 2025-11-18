import 'package:json_annotation/json_annotation.dart';

part 'field.g.dart';

@JsonSerializable()
class Field {
  final int id;
  final int farm;
  @JsonKey(name: 'farm_name')
  final String? farmName;
  final String name;
  final double area;
  @JsonKey(name: 'soil_type')
  final String soilType;
  final int? crop;
  @JsonKey(name: 'crop_name')
  final String? cropName;
  @JsonKey(name: 'planting_date')
  final DateTime? plantingDate;
  @JsonKey(name: 'expected_harvest_date')
  final DateTime? expectedHarvestDate;
  final String status;
  final String? notes;
  @JsonKey(name: 'devices_count')
  final int? devicesCount;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  @JsonKey(name: 'updated_at')
  final DateTime updatedAt;

  Field({
    required this.id,
    required this.farm,
    this.farmName,
    required this.name,
    required this.area,
    required this.soilType,
    this.crop,
    this.cropName,
    this.plantingDate,
    this.expectedHarvestDate,
    required this.status,
    this.notes,
    this.devicesCount,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Field.fromJson(Map<String, dynamic> json) => _$FieldFromJson(json);
  Map<String, dynamic> toJson() => _$FieldToJson(this);
}

@JsonSerializable()
class IrrigationSchedule {
  final int id;
  final int field;
  @JsonKey(name: 'scheduled_time')
  final DateTime scheduledTime;
  final int duration;
  @JsonKey(name: 'water_amount')
  final double? waterAmount;
  final String status;
  @JsonKey(name: 'completed_at')
  final DateTime? completedAt;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;

  IrrigationSchedule({
    required this.id,
    required this.field,
    required this.scheduledTime,
    required this.duration,
    this.waterAmount,
    required this.status,
    this.completedAt,
    required this.createdAt,
  });

  factory IrrigationSchedule.fromJson(Map<String, dynamic> json) =>
      _$IrrigationScheduleFromJson(json);
  Map<String, dynamic> toJson() => _$IrrigationScheduleToJson(this);
}
