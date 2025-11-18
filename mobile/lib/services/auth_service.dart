import 'package:dio/dio.dart';
import '../models/user.dart';
import '../utils/constants.dart';
import 'api_client.dart';

class AuthService {
  final ApiClient _apiClient;

  AuthService(this._apiClient);

  Future<LoginResponse> login(String username, String password) async {
    try {
      final response = await _apiClient.dio.post(
        '${AppConstants.authUrl}/login/',
        data: {
          'username': username,
          'password': password,
        },
      );

      final loginResponse = LoginResponse.fromJson(response.data);
      await _apiClient.saveTokens(loginResponse.access, loginResponse.refresh);
      return loginResponse;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<User> register(RegisterRequest request) async {
    try {
      final response = await _apiClient.dio.post(
        '/users/',
        data: request.toJson(),
      );
      return User.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<User> getCurrentUser() async {
    try {
      final response = await _apiClient.dio.get('/users/me/');
      return User.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<void> logout() async {
    await _apiClient.clearTokens();
  }

  Future<bool> isLoggedIn() async {
    final token = await _apiClient.getAccessToken();
    return token != null;
  }

  String _handleError(DioException error) {
    if (error.response != null) {
      final data = error.response!.data;
      if (data is Map && data.containsKey('error')) {
        return data['error'];
      }
      if (data is Map && data.containsKey('detail')) {
        return data['detail'];
      }
      return 'حدث خطأ: ${error.response!.statusCode}';
    }
    return 'فشل الاتصال بالخادم';
  }
}
