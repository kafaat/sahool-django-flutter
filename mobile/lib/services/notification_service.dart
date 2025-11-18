import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'dart:io' show Platform;

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();

  bool _initialized = false;

  /// تهيئة خدمة الإشعارات
  Future<void> initialize() async {
    if (_initialized) return;

    // طلب الأذونات
    await _requestPermissions();

    // تهيئة الإشعارات المحلية
    await _initializeLocalNotifications();

    // تهيئة Firebase Messaging
    await _initializeFirebaseMessaging();

    _initialized = true;
  }

  /// طلب أذونات الإشعارات
  Future<void> _requestPermissions() async {
    if (Platform.isIOS) {
      await _firebaseMessaging.requestPermission(
        alert: true,
        badge: true,
        sound: true,
        provisional: false,
      );
    }

    final settings = await _firebaseMessaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      announcement: false,
      carPlay: false,
      criticalAlert: false,
      provisional: false,
    );

    print('أذونات الإشعارات: ${settings.authorizationStatus}');
  }

  /// تهيئة الإشعارات المحلية
  Future<void> _initializeLocalNotifications() async {
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _localNotifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _onNotificationTapped,
    );
  }

  /// تهيئة Firebase Messaging
  Future<void> _initializeFirebaseMessaging() async {
    // الحصول على FCM Token
    final token = await _firebaseMessaging.getToken();
    print('FCM Token: $token');
    // TODO: إرسال Token إلى Backend

    // الاستماع لتحديثات Token
    _firebaseMessaging.onTokenRefresh.listen((newToken) {
      print('FCM Token Updated: $newToken');
      // TODO: تحديث Token في Backend
    });

    // معالجة الإشعارات عندما يكون التطبيق في المقدمة
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

    // معالجة الإشعارات عند النقر عليها (التطبيق في الخلفية)
    FirebaseMessaging.onMessageOpenedApp.listen(_handleMessageOpenedApp);

    // معالجة الإشعارات عند فتح التطبيق من إشعار (التطبيق مغلق)
    final initialMessage = await _firebaseMessaging.getInitialMessage();
    if (initialMessage != null) {
      _handleMessageOpenedApp(initialMessage);
    }
  }

  /// معالجة الإشعارات في المقدمة
  Future<void> _handleForegroundMessage(RemoteMessage message) async {
    print('رسالة في المقدمة: ${message.messageId}');

    // عرض إشعار محلي
    await _showLocalNotification(
      title: message.notification?.title ?? 'إشعار جديد',
      body: message.notification?.body ?? '',
      payload: message.data.toString(),
    );
  }

  /// معالجة النقر على الإشعار
  void _handleMessageOpenedApp(RemoteMessage message) {
    print('تم النقر على الإشعار: ${message.messageId}');
    
    // التنقل بناءً على نوع الإشعار
    final notificationType = message.data['type'];
    
    switch (notificationType) {
      case 'irrigation':
        // الانتقال إلى شاشة الري
        break;
      case 'disease':
        // الانتقال إلى شاشة الأمراض
        break;
      case 'marketplace':
        // الانتقال إلى Marketplace
        break;
      default:
        // الانتقال إلى الشاشة الرئيسية
        break;
    }
  }

  /// معالجة النقر على الإشعار المحلي
  void _onNotificationTapped(NotificationResponse response) {
    print('تم النقر على الإشعار المحلي: ${response.payload}');
    // معالجة النقر
  }

  /// عرض إشعار محلي
  Future<void> _showLocalNotification({
    required String title,
    required String body,
    String? payload,
  }) async {
    const androidDetails = AndroidNotificationDetails(
      'sahool_channel',
      'سهول',
      channelDescription: 'إشعارات منصة سهول الذكية',
      importance: Importance.high,
      priority: Priority.high,
      showWhen: true,
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    const details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await _localNotifications.show(
      DateTime.now().millisecond,
      title,
      body,
      details,
      payload: payload,
    );
  }

  /// إرسال إشعار تنبيه الري
  Future<void> sendIrrigationAlert({
    required String fieldName,
    required String message,
  }) async {
    await _showLocalNotification(
      title: 'تنبيه ري - $fieldName',
      body: message,
      payload: 'irrigation',
    );
  }

  /// إرسال إشعار كشف مرض
  Future<void> sendDiseaseAlert({
    required String diseaseName,
    required String severity,
  }) async {
    await _showLocalNotification(
      title: 'تنبيه مرض: $diseaseName',
      body: 'مستوى الخطورة: $severity',
      payload: 'disease',
    );
  }

  /// إرسال إشعار عرض جديد في Marketplace
  Future<void> sendMarketplaceOffer({
    required String buyerName,
    required String cropName,
  }) async {
    await _showLocalNotification(
      title: 'عرض جديد',
      body: '$buyerName قدم عرضاً على $cropName',
      payload: 'marketplace',
    );
  }

  /// الحصول على FCM Token
  Future<String?> getToken() async {
    return await _firebaseMessaging.getToken();
  }

  /// حذف Token
  Future<void> deleteToken() async {
    await _firebaseMessaging.deleteToken();
  }

  /// الاشتراك في موضوع
  Future<void> subscribeToTopic(String topic) async {
    await _firebaseMessaging.subscribeToTopic(topic);
    print('تم الاشتراك في: $topic');
  }

  /// إلغاء الاشتراك من موضوع
  Future<void> unsubscribeFromTopic(String topic) async {
    await _firebaseMessaging.unsubscribeFromTopic(topic);
    print('تم إلغاء الاشتراك من: $topic');
  }
}

/// معالج الإشعارات في الخلفية (يجب أن يكون دالة عامة)
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  print('معالجة رسالة في الخلفية: ${message.messageId}');
}
