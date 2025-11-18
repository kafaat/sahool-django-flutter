import 'package:dio/dio.dart';
import '../models/iot_device.dart';
import 'api_client.dart';

class IoTService {
  final ApiClient _apiClient;

  IoTService(this._apiClient);

  Future<List<IoTDevice>> getDevices({int? fieldId, int page = 1}) async {
    try {
      final queryParams = {'page': page};
      if (fieldId != null) queryParams['field'] = fieldId.toString();

      final response = await _apiClient.dio.get(
        '/iot-devices/',
        queryParameters: queryParams,
      );
      final List<dynamic> results = response.data['results'] ?? response.data;
      return results.map((json) => IoTDevice.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<IoTDevice> getDevice(int id) async {
    try {
      final response = await _apiClient.dio.get('/iot-devices/$id/');
      return IoTDevice.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<void> updateDeviceStatus(int id, String status) async {
    try {
      await _apiClient.dio.post(
        '/iot-devices/$id/update_status/',
        data: {'status': status},
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<List<Sensor>> getSensors(int deviceId) async {
    try {
      final response = await _apiClient.dio.get(
        '/sensors/',
        queryParameters: {'device': deviceId},
      );
      final List<dynamic> results = response.data['results'] ?? response.data;
      return results.map((json) => Sensor.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<List<SensorReading>> getSensorReadings(int sensorId,
      {int limit = 100}) async {
    try {
      final response = await _apiClient.dio.get(
        '/sensors/$sensorId/readings/',
        queryParameters: {'limit': limit},
      );
      final List<dynamic> data = response.data;
      return data.map((json) => SensorReading.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<List<Actuator>> getActuators(int deviceId) async {
    try {
      final response = await _apiClient.dio.get(
        '/actuators/',
        queryParameters: {'device': deviceId},
      );
      final List<dynamic> results = response.data['results'] ?? response.data;
      return results.map((json) => Actuator.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<void> activateActuator(int id) async {
    try {
      await _apiClient.dio.post('/actuators/$id/activate/');
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<void> deactivateActuator(int id) async {
    try {
      await _apiClient.dio.post('/actuators/$id/deactivate/');
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  String _handleError(DioException error) {
    if (error.response != null) {
      return 'حدث خطأ: ${error.response!.statusCode}';
    }
    return 'فشل الاتصال بالخادم';
  }
}
