import 'package:json_annotation/json_annotation.dart';

part 'farm.g.dart';

@JsonSerializable()
class Farm {
  final int id;
  final int owner;
  @JsonKey(name: 'owner_name')
  final String? ownerName;
  final String name;
  final String location;
  final double? latitude;
  final double? longitude;
  @JsonKey(name: 'total_area')
  final double totalArea;
  final String? description;
  final String? image;
  @JsonKey(name: 'fields_count')
  final int? fieldsCount;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  @JsonKey(name: 'updated_at')
  final DateTime updatedAt;

  Farm({
    required this.id,
    required this.owner,
    this.ownerName,
    required this.name,
    required this.location,
    this.latitude,
    this.longitude,
    required this.totalArea,
    this.description,
    this.image,
    this.fieldsCount,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Farm.fromJson(Map<String, dynamic> json) => _$FarmFromJson(json);
  Map<String, dynamic> toJson() => _$FarmToJson(this);
}

@JsonSerializable()
class Crop {
  final int id;
  final String name;
  final String? variety;
  @JsonKey(name: 'growth_duration')
  final int? growthDuration;
  @JsonKey(name: 'water_requirement')
  final String? waterRequirement;
  final String? description;

  Crop({
    required this.id,
    required this.name,
    this.variety,
    this.growthDuration,
    this.waterRequirement,
    this.description,
  });

  factory Crop.fromJson(Map<String, dynamic> json) => _$CropFromJson(json);
  Map<String, dynamic> toJson() => _$CropToJson(this);
}
