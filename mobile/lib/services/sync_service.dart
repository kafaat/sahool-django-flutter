import 'package:connectivity_plus/connectivity_plus.dart';
import 'dart:async';
import 'offline_storage.dart';
import 'api_client.dart';

class SyncService {
  static final SyncService _instance = SyncService._internal();
  factory SyncService() => _instance;
  SyncService._internal();

  final OfflineStorage _offlineStorage = OfflineStorage();
  final Connectivity _connectivity = Connectivity();
  
  StreamSubscription? _connectivitySubscription;
  bool _isSyncing = false;
  bool _isOnline = false;

  /// تهيئة خدمة المزامنة
  Future<void> initialize() async {
    // التحقق من الاتصال الأولي
    final result = await _connectivity.checkConnectivity();
    _isOnline = result != ConnectivityResult.none;

    // الاستماع لتغييرات الاتصال
    _connectivitySubscription = _connectivity.onConnectivityChanged.listen(
      (result) {
        final wasOnline = _isOnline;
        _isOnline = result != ConnectivityResult.none;

        // إذا أصبح متصلاً بعد انقطاع، قم بالمزامنة
        if (!wasOnline && _isOnline) {
          print('تم استعادة الاتصال - بدء المزامنة');
          syncPendingOperations();
        }
      },
    );
  }

  /// التحقق من حالة الاتصال
  bool get isOnline => _isOnline;

  /// مزامنة العمليات المعلقة
  Future<void> syncPendingOperations() async {
    if (_isSyncing || !_isOnline) return;

    _isSyncing = true;
    print('بدء مزامنة العمليات المعلقة...');

    try {
      final operations = _offlineStorage.getPendingOperations();
      print('عدد العمليات المعلقة: ${operations.length}');

      for (var operation in operations) {
        try {
          await _executeOperation(operation);
          
          // حذف العملية بعد النجاح
          final timestamp = operation['timestamp'] as int;
          await _offlineStorage.deletePendingOperation(timestamp);
          
          print('تمت مزامنة العملية: ${operation['type']}');
        } catch (e) {
          print('فشلت مزامنة العملية: ${operation['type']} - $e');
          // الاحتفاظ بالعملية للمحاولة لاحقاً
        }
      }

      print('انتهت المزامنة');
    } catch (e) {
      print('خطأ في المزامنة: $e');
    } finally {
      _isSyncing = false;
    }
  }

  /// تنفيذ عملية معلقة
  Future<void> _executeOperation(Map<String, dynamic> operation) async {
    final type = operation['type'] as String;
    final data = operation['data'] as Map<String, dynamic>;

    switch (type) {
      case 'create_farm':
        // إنشاء مزرعة
        // await apiClient.post('/farms/', data: data);
        break;
      
      case 'update_farm':
        final id = operation['id'] as int;
        // await apiClient.put('/farms/$id/', data: data);
        break;
      
      case 'delete_farm':
        final id = operation['id'] as int;
        // await apiClient.delete('/farms/$id/');
        break;
      
      case 'create_field':
        // await apiClient.post('/fields/', data: data);
        break;
      
      case 'update_field':
        final id = operation['id'] as int;
        // await apiClient.put('/fields/$id/', data: data);
        break;
      
      case 'delete_field':
        final id = operation['id'] as int;
        // await apiClient.delete('/fields/$id/');
        break;
      
      default:
        print('نوع عملية غير معروف: $type');
    }
  }

  /// إضافة عملية إلى قائمة الانتظار
  Future<void> queueOperation({
    required String type,
    required Map<String, dynamic> data,
    int? id,
  }) async {
    final operation = {
      'type': type,
      'data': data,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
    };

    if (id != null) {
      operation['id'] = id;
    }

    await _offlineStorage.addPendingOperation(operation);
    print('تمت إضافة العملية إلى قائمة الانتظار: $type');

    // محاولة المزامنة فوراً إذا كان متصلاً
    if (_isOnline) {
      syncPendingOperations();
    }
  }

  /// مزامنة البيانات من الخادم
  Future<void> syncFromServer(ApiClient apiClient) async {
    if (!_isOnline) {
      print('غير متصل - تخطي المزامنة من الخادم');
      return;
    }

    try {
      print('بدء مزامنة البيانات من الخادم...');

      // مزامنة المزارع
      // final farmsResponse = await apiClient.get('/farms/');
      // final farms = (farmsResponse.data as List)
      //     .map((json) => Farm.fromJson(json))
      //     .toList();
      // await _offlineStorage.saveFarms(farms);

      // مزامنة الحقول
      // final fieldsResponse = await apiClient.get('/fields/');
      // final fields = (fieldsResponse.data as List)
      //     .map((json) => Field.fromJson(json))
      //     .toList();
      // await _offlineStorage.saveFields(fields);

      // مزامنة الأجهزة
      // final devicesResponse = await apiClient.get('/iot-devices/');
      // final devices = (devicesResponse.data as List)
      //     .map((json) => IoTDevice.fromJson(json))
      //     .toList();
      // await _offlineStorage.saveDevices(devices);

      print('انتهت المزامنة من الخادم');
    } catch (e) {
      print('خطأ في المزامنة من الخادم: $e');
      rethrow;
    }
  }

  /// الحصول على عدد العمليات المعلقة
  int getPendingOperationsCount() {
    return _offlineStorage.getPendingOperationsCount();
  }

  /// مسح جميع العمليات المعلقة
  Future<void> clearPendingOperations() async {
    await _offlineStorage.clearPendingOperations();
  }

  /// إيقاف الخدمة
  void dispose() {
    _connectivitySubscription?.cancel();
  }
}
