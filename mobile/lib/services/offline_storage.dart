import 'package:hive_flutter/hive_flutter.dart';
import '../models/farm.dart';
import '../models/field.dart';
import '../models/iot_device.dart';

class OfflineStorage {
  static final OfflineStorage _instance = OfflineStorage._internal();
  factory OfflineStorage() => _instance;
  OfflineStorage._internal();

  // أسماء الصناديق
  static const String _farmsBox = 'farms';
  static const String _fieldsBox = 'fields';
  static const String _devicesBox = 'devices';
  static const String _pendingOperationsBox = 'pending_operations';
  static const String _cacheBox = 'cache';

  bool _initialized = false;

  /// تهيئة Hive
  Future<void> initialize() async {
    if (_initialized) return;

    await Hive.initFlutter();

    // تسجيل المحولات (Adapters)
    // Hive.registerAdapter(FarmAdapter());
    // Hive.registerAdapter(FieldAdapter());
    // Hive.registerAdapter(IoTDeviceAdapter());

    // فتح الصناديق
    await Hive.openBox(_farmsBox);
    await Hive.openBox(_fieldsBox);
    await Hive.openBox(_devicesBox);
    await Hive.openBox(_pendingOperationsBox);
    await Hive.openBox(_cacheBox);

    _initialized = true;
  }

  // ==================== المزارع ====================

  /// حفظ مزرعة
  Future<void> saveFarm(Farm farm) async {
    final box = Hive.box(_farmsBox);
    await box.put(farm.id, farm.toJson());
  }

  /// حفظ قائمة مزارع
  Future<void> saveFarms(List<Farm> farms) async {
    final box = Hive.box(_farmsBox);
    final Map<int, Map<String, dynamic>> farmsMap = {};
    for (var farm in farms) {
      farmsMap[farm.id] = farm.toJson();
    }
    await box.putAll(farmsMap);
  }

  /// الحصول على مزرعة
  Farm? getFarm(int id) {
    final box = Hive.box(_farmsBox);
    final data = box.get(id);
    if (data != null) {
      return Farm.fromJson(Map<String, dynamic>.from(data));
    }
    return null;
  }

  /// الحصول على جميع المزارع
  List<Farm> getAllFarms() {
    final box = Hive.box(_farmsBox);
    return box.values
        .map((data) => Farm.fromJson(Map<String, dynamic>.from(data)))
        .toList();
  }

  /// حذف مزرعة
  Future<void> deleteFarm(int id) async {
    final box = Hive.box(_farmsBox);
    await box.delete(id);
  }

  // ==================== الحقول ====================

  /// حفظ حقل
  Future<void> saveField(Field field) async {
    final box = Hive.box(_fieldsBox);
    await box.put(field.id, field.toJson());
  }

  /// حفظ قائمة حقول
  Future<void> saveFields(List<Field> fields) async {
    final box = Hive.box(_fieldsBox);
    final Map<int, Map<String, dynamic>> fieldsMap = {};
    for (var field in fields) {
      fieldsMap[field.id] = field.toJson();
    }
    await box.putAll(fieldsMap);
  }

  /// الحصول على حقل
  Field? getField(int id) {
    final box = Hive.box(_fieldsBox);
    final data = box.get(id);
    if (data != null) {
      return Field.fromJson(Map<String, dynamic>.from(data));
    }
    return null;
  }

  /// الحصول على حقول مزرعة
  List<Field> getFieldsByFarm(int farmId) {
    final box = Hive.box(_fieldsBox);
    return box.values
        .map((data) => Field.fromJson(Map<String, dynamic>.from(data)))
        .where((field) => field.farmId == farmId)
        .toList();
  }

  /// الحصول على جميع الحقول
  List<Field> getAllFields() {
    final box = Hive.box(_fieldsBox);
    return box.values
        .map((data) => Field.fromJson(Map<String, dynamic>.from(data)))
        .toList();
  }

  /// حذف حقل
  Future<void> deleteField(int id) async {
    final box = Hive.box(_fieldsBox);
    await box.delete(id);
  }

  // ==================== أجهزة IoT ====================

  /// حفظ جهاز
  Future<void> saveDevice(IoTDevice device) async {
    final box = Hive.box(_devicesBox);
    await box.put(device.id, device.toJson());
  }

  /// حفظ قائمة أجهزة
  Future<void> saveDevices(List<IoTDevice> devices) async {
    final box = Hive.box(_devicesBox);
    final Map<int, Map<String, dynamic>> devicesMap = {};
    for (var device in devices) {
      devicesMap[device.id] = device.toJson();
    }
    await box.putAll(devicesMap);
  }

  /// الحصول على جهاز
  IoTDevice? getDevice(int id) {
    final box = Hive.box(_devicesBox);
    final data = box.get(id);
    if (data != null) {
      return IoTDevice.fromJson(Map<String, dynamic>.from(data));
    }
    return null;
  }

  /// الحصول على أجهزة حقل
  List<IoTDevice> getDevicesByField(int fieldId) {
    final box = Hive.box(_devicesBox);
    return box.values
        .map((data) => IoTDevice.fromJson(Map<String, dynamic>.from(data)))
        .where((device) => device.fieldId == fieldId)
        .toList();
  }

  /// الحصول على جميع الأجهزة
  List<IoTDevice> getAllDevices() {
    final box = Hive.box(_devicesBox);
    return box.values
        .map((data) => IoTDevice.fromJson(Map<String, dynamic>.from(data)))
        .toList();
  }

  /// حذف جهاز
  Future<void> deleteDevice(int id) async {
    final box = Hive.box(_devicesBox);
    await box.delete(id);
  }

  // ==================== العمليات المعلقة ====================

  /// إضافة عملية معلقة
  Future<void> addPendingOperation(Map<String, dynamic> operation) async {
    final box = Hive.box(_pendingOperationsBox);
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    await box.put(timestamp, operation);
  }

  /// الحصول على جميع العمليات المعلقة
  List<Map<String, dynamic>> getPendingOperations() {
    final box = Hive.box(_pendingOperationsBox);
    return box.values
        .map((data) => Map<String, dynamic>.from(data))
        .toList();
  }

  /// حذف عملية معلقة
  Future<void> deletePendingOperation(int timestamp) async {
    final box = Hive.box(_pendingOperationsBox);
    await box.delete(timestamp);
  }

  /// مسح جميع العمليات المعلقة
  Future<void> clearPendingOperations() async {
    final box = Hive.box(_pendingOperationsBox);
    await box.clear();
  }

  /// عدد العمليات المعلقة
  int getPendingOperationsCount() {
    final box = Hive.box(_pendingOperationsBox);
    return box.length;
  }

  // ==================== التخزين المؤقت (Cache) ====================

  /// حفظ في الذاكرة المؤقتة
  Future<void> cacheData(String key, dynamic data, {Duration? ttl}) async {
    final box = Hive.box(_cacheBox);
    final cacheEntry = {
      'data': data,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
      'ttl': ttl?.inMilliseconds,
    };
    await box.put(key, cacheEntry);
  }

  /// الحصول من الذاكرة المؤقتة
  dynamic getCachedData(String key) {
    final box = Hive.box(_cacheBox);
    final cacheEntry = box.get(key);
    
    if (cacheEntry == null) return null;

    final entry = Map<String, dynamic>.from(cacheEntry);
    final timestamp = entry['timestamp'] as int;
    final ttl = entry['ttl'] as int?;

    // التحقق من انتهاء الصلاحية
    if (ttl != null) {
      final now = DateTime.now().millisecondsSinceEpoch;
      if (now - timestamp > ttl) {
        // انتهت الصلاحية
        box.delete(key);
        return null;
      }
    }

    return entry['data'];
  }

  /// حذف من الذاكرة المؤقتة
  Future<void> deleteCachedData(String key) async {
    final box = Hive.box(_cacheBox);
    await box.delete(key);
  }

  /// مسح الذاكرة المؤقتة
  Future<void> clearCache() async {
    final box = Hive.box(_cacheBox);
    await box.clear();
  }

  // ==================== إدارة عامة ====================

  /// مسح جميع البيانات المحلية
  Future<void> clearAll() async {
    await Hive.box(_farmsBox).clear();
    await Hive.box(_fieldsBox).clear();
    await Hive.box(_devicesBox).clear();
    await Hive.box(_pendingOperationsBox).clear();
    await Hive.box(_cacheBox).clear();
  }

  /// الحصول على حجم التخزين
  Map<String, int> getStorageSize() {
    return {
      'farms': Hive.box(_farmsBox).length,
      'fields': Hive.box(_fieldsBox).length,
      'devices': Hive.box(_devicesBox).length,
      'pending_operations': Hive.box(_pendingOperationsBox).length,
      'cache': Hive.box(_cacheBox).length,
    };
  }

  /// إغلاق جميع الصناديق
  Future<void> close() async {
    await Hive.close();
    _initialized = false;
  }
}
