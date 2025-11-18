import 'package:dio/dio.dart';
import '../models/farm.dart';
import 'api_client.dart';

class FarmService {
  final ApiClient _apiClient;

  FarmService(this._apiClient);

  Future<List<Farm>> getFarms({int page = 1}) async {
    try {
      final response = await _apiClient.dio.get(
        '/farms/',
        queryParameters: {'page': page},
      );
      final List<dynamic> results = response.data['results'] ?? response.data;
      return results.map((json) => Farm.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Farm> getFarm(int id) async {
    try {
      final response = await _apiClient.dio.get('/farms/$id/');
      return Farm.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Farm> createFarm(Map<String, dynamic> data) async {
    try {
      final response = await _apiClient.dio.post('/farms/', data: data);
      return Farm.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Farm> updateFarm(int id, Map<String, dynamic> data) async {
    try {
      final response = await _apiClient.dio.put('/farms/$id/', data: data);
      return Farm.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<void> deleteFarm(int id) async {
    try {
      await _apiClient.dio.delete('/farms/$id/');
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getFarmStatistics(int id) async {
    try {
      final response = await _apiClient.dio.get('/farms/$id/statistics/');
      return response.data;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<List<Crop>> getCrops() async {
    try {
      final response = await _apiClient.dio.get('/crops/');
      final List<dynamic> results = response.data['results'] ?? response.data;
      return results.map((json) => Crop.fromJson(json)).toList();
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
