# 🌟 الميزات الإضافية المتقدمة - منصة سهول

## 📋 نظرة عامة

تم إضافة أربع ميزات إضافية متقدمة تكمل النظام وتجعله منصة شاملة:

1. **🌐 نظام Marketplace** - لتجارة المحاصيل
2. **🗺️ Google Maps Integration** - للخرائط التفاعلية
3. **📱 Push Notifications** - للتنبيهات الذكية
4. **💾 Offline Support** - للعمل بدون إنترنت

---

## 1. 🌐 نظام Marketplace لتجارة المحاصيل

### الوصف
منصة متكاملة لبيع وشراء المحاصيل الزراعية مباشرة بين المزارعين والمشترين.

### النماذج (Models)

#### CropListing (إعلان محصول)
```python
- البائع (seller)
- العنوان والوصف
- نوع المحصول والكمية
- السعر لكل كجم
- درجة الجودة (ممتاز، درجة أولى، ثانية، عادي)
- تاريخ التوفر والانتهاء
- الموقع (مع إحداثيات GPS)
- الحالة (نشط، مباع، منتهي، ملغي)
- الصور
- عدد المشاهدات
```

#### Offer (عرض شراء)
```python
- الإعلان المرتبط
- المشتري
- الكمية المطلوبة
- السعر المعروض
- رسالة
- الحالة (قيد الانتظار، مقبول، مرفوض، ملغي)
```

#### Transaction (معاملة)
```python
- الإعلان والعرض
- البائع والمشتري
- الكمية والسعر
- المبلغ الإجمالي
- الحالة (قيد الانتظار، مؤكد، قيد التوصيل، مكتمل، ملغي)
- عنوان وتاريخ التوصيل
- ملاحظات
```

#### Review (تقييم)
```python
- المعاملة المرتبطة
- المقيّم والمستخدم المقيّم
- التقييم (1-5 نجوم)
- التعليق
```

### API Endpoints

#### إعلانات المحاصيل
```
GET    /api/marketplace/listings/              # قائمة الإعلانات
POST   /api/marketplace/listings/              # إنشاء إعلان
GET    /api/marketplace/listings/{id}/         # تفاصيل إعلان
PUT    /api/marketplace/listings/{id}/         # تحديث إعلان
DELETE /api/marketplace/listings/{id}/         # حذف إعلان

GET    /api/marketplace/listings/my_listings/  # إعلاناتي
GET    /api/marketplace/listings/active_listings/ # الإعلانات النشطة
POST   /api/marketplace/listings/{id}/mark_sold/ # تحديد كمباع
```

#### العروض
```
GET    /api/marketplace/offers/                # قائمة العروض
POST   /api/marketplace/offers/                # إنشاء عرض
GET    /api/marketplace/offers/{id}/           # تفاصيل عرض
PUT    /api/marketplace/offers/{id}/           # تحديث عرض
DELETE /api/marketplace/offers/{id}/           # حذف عرض

GET    /api/marketplace/offers/my_offers/      # عروضي
GET    /api/marketplace/offers/received_offers/ # العروض المستلمة
POST   /api/marketplace/offers/{id}/accept/    # قبول عرض
POST   /api/marketplace/offers/{id}/reject/    # رفض عرض
```

#### المعاملات
```
GET    /api/marketplace/transactions/          # قائمة المعاملات
GET    /api/marketplace/transactions/{id}/     # تفاصيل معاملة
PUT    /api/marketplace/transactions/{id}/     # تحديث معاملة

GET    /api/marketplace/transactions/my_sales/ # مبيعاتي
GET    /api/marketplace/transactions/my_purchases/ # مشترياتي
POST   /api/marketplace/transactions/{id}/confirm/ # تأكيد معاملة
POST   /api/marketplace/transactions/{id}/mark_delivered/ # تحديد كمُسلّم
POST   /api/marketplace/transactions/{id}/complete/ # إكمال معاملة
```

#### التقييمات
```
GET    /api/marketplace/reviews/               # قائمة التقييمات
POST   /api/marketplace/reviews/               # إنشاء تقييم
GET    /api/marketplace/reviews/{id}/          # تفاصيل تقييم

GET    /api/marketplace/reviews/user_rating/?user_id={id} # تقييم مستخدم
```

### الميزات

✅ **إعلانات ذكية** مع صور ومواقع GPS
✅ **نظام عروض** قابل للتفاوض
✅ **تتبع المعاملات** من البداية للنهاية
✅ **نظام تقييم** للبائعين والمشترين
✅ **بحث وفلترة** متقدمة
✅ **إحصائيات** للمستخدمين

---

## 2. 🗺️ Google Maps Integration

### الوصف
تكامل كامل مع Google Maps لعرض المزارع والحقول على الخريطة.

### الملفات
- `mobile/lib/screens/maps/farms_map_screen.dart`

### الميزات

✅ **عرض المزارع** على الخريطة مع علامات مخصصة
✅ **الموقع الحالي** للمستخدم
✅ **معلومات تفصيلية** عند النقر على العلامة
✅ **الاتجاهات** إلى المزرعة
✅ **إضافة مزرعة** من الخريطة
✅ **تحديد الموقع** بدقة GPS

### الاستخدام

```dart
import 'package:sahool_mobile/screens/maps/farms_map_screen.dart';

// الانتقال إلى خريطة المزارع
Navigator.push(
  context,
  MaterialPageRoute(
    builder: (_) => FarmsMapScreen(),
  ),
);
```

### المكتبات المطلوبة

```yaml
dependencies:
  google_maps_flutter: ^2.5.0
  geolocator: ^10.1.0
  geocoding: ^2.1.1
```

### الأذونات المطلوبة

**Android** (`android/app/src/main/AndroidManifest.xml`):
```xml
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />

<meta-data
    android:name="com.google.android.geo.API_KEY"
    android:value="YOUR_API_KEY_HERE"/>
```

**iOS** (`ios/Runner/Info.plist`):
```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>نحتاج إلى موقعك لعرض المزارع القريبة</string>
<key>NSLocationAlwaysUsageDescription</key>
<string>نحتاج إلى موقعك لعرض المزارع القريبة</string>
```

---

## 3. 📱 Push Notifications

### الوصف
نظام إشعارات متكامل باستخدام Firebase Cloud Messaging.

### الملفات
- `mobile/lib/services/notification_service.dart`

### الميزات

✅ **إشعارات فورية** (Foreground)
✅ **إشعارات خلفية** (Background)
✅ **إشعارات محلية** (Local Notifications)
✅ **معالجة النقر** على الإشعارات
✅ **Topics** للاشتراك الجماعي
✅ **أنواع إشعارات** متخصصة

### أنواع الإشعارات

#### 1. تنبيه الري
```dart
await NotificationService().sendIrrigationAlert(
  fieldName: 'حقل الطماطم',
  message: 'حان وقت الري - رطوبة التربة منخفضة',
);
```

#### 2. تنبيه المرض
```dart
await NotificationService().sendDiseaseAlert(
  diseaseName: 'اللفحة المبكرة',
  severity: 'متوسط',
);
```

#### 3. عرض Marketplace
```dart
await NotificationService().sendMarketplaceOffer(
  buyerName: 'أحمد محمد',
  cropName: 'طماطم - 500 كجم',
);
```

### الإعداد

#### 1. إضافة Firebase إلى المشروع

**Android** (`android/app/google-services.json`):
- تحميل من Firebase Console

**iOS** (`ios/Runner/GoogleService-Info.plist`):
- تحميل من Firebase Console

#### 2. المكتبات المطلوبة

```yaml
dependencies:
  firebase_core: ^2.24.2
  firebase_messaging: ^14.7.9
  flutter_local_notifications: ^16.3.0
```

#### 3. التهيئة في main.dart

```dart
import 'package:firebase_core/firebase_core.dart';
import 'services/notification_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // تهيئة Firebase
  await Firebase.initializeApp();
  
  // تهيئة الإشعارات
  await NotificationService().initialize();
  
  // معالج الإشعارات في الخلفية
  FirebaseMessaging.onBackgroundMessage(
    firebaseMessagingBackgroundHandler
  );
  
  runApp(MyApp());
}
```

---

## 4. 💾 Offline Support

### الوصف
نظام متكامل للعمل بدون إنترنت مع مزامنة تلقائية.

### الملفات
- `mobile/lib/services/offline_storage.dart` - التخزين المحلي
- `mobile/lib/services/sync_service.dart` - المزامنة

### الميزات

✅ **تخزين محلي** باستخدام Hive
✅ **قائمة انتظار** للعمليات المعلقة
✅ **مزامنة تلقائية** عند استعادة الاتصال
✅ **ذاكرة مؤقتة** (Cache) مع TTL
✅ **كشف الاتصال** التلقائي

### البيانات المخزنة محلياً

- المزارع (Farms)
- الحقول (Fields)
- أجهزة IoT (Devices)
- العمليات المعلقة (Pending Operations)
- الذاكرة المؤقتة (Cache)

### الاستخدام

#### 1. حفظ بيانات

```dart
final storage = OfflineStorage();

// حفظ مزرعة
await storage.saveFarm(farm);

// حفظ قائمة مزارع
await storage.saveFarms(farmsList);
```

#### 2. استرجاع بيانات

```dart
// الحصول على مزرعة
final farm = storage.getFarm(farmId);

// الحصول على جميع المزارع
final farms = storage.getAllFarms();
```

#### 3. إضافة عملية معلقة

```dart
final sync = SyncService();

// إضافة عملية إنشاء مزرعة
await sync.queueOperation(
  type: 'create_farm',
  data: farm.toJson(),
);
```

#### 4. المزامنة

```dart
// مزامنة يدوية
await sync.syncPendingOperations();

// مزامنة من الخادم
await sync.syncFromServer(apiClient);

// عدد العمليات المعلقة
final count = sync.getPendingOperationsCount();
```

### المكتبات المطلوبة

```yaml
dependencies:
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  connectivity_plus: ^5.0.2

dev_dependencies:
  hive_generator: ^2.0.1
  build_runner: ^2.4.7
```

### التهيئة

```dart
import 'services/offline_storage.dart';
import 'services/sync_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // تهيئة التخزين المحلي
  await OfflineStorage().initialize();
  
  // تهيئة المزامنة
  await SyncService().initialize();
  
  runApp(MyApp());
}
```

---

## 📊 الإحصائيات الإجمالية

### Backend
- **ملفات جديدة**: 4 (Marketplace)
- **Models**: 4 (CropListing, Offer, Transaction, Review)
- **API Endpoints**: 20+
- **أسطر كود**: ~1,500 سطر

### Flutter
- **ملفات جديدة**: 4
- **Screens**: 1 (Maps)
- **Services**: 3 (Notifications, Offline, Sync)
- **أسطر كود**: ~1,200 سطر

---

## 🚀 الخطوات التالية

### قريباً
1. [ ] واجهات Flutter لـ Marketplace
2. [ ] تكامل حقيقي مع Firebase
3. [ ] Hive Adapters للنماذج
4. [ ] اختبارات شاملة

### المستقبل
1. [ ] نظام الدفع الإلكتروني
2. [ ] التأمين على المحاصيل
3. [ ] نظام القروض الزراعية
4. [ ] Blockchain للتتبع

---

## 💡 ملاحظات مهمة

### Marketplace
- يحتاج إلى نظام دفع (Stripe/PayPal)
- يحتاج إلى نظام توصيل
- يحتاج إلى نظام ضمان

### Google Maps
- يحتاج إلى API Key من Google Cloud
- الأذونات مطلوبة للموقع
- استهلاك البطارية عند الاستخدام المستمر

### Push Notifications
- يحتاج إلى Firebase Project
- iOS يحتاج إلى APNs Certificate
- Android يحتاج إلى google-services.json

### Offline Support
- حجم التخزين محدود
- المزامنة تستهلك بيانات
- التعارضات تحتاج معالجة يدوية

---

## 📚 المراجع

1. **Django REST Framework** - API Development
2. **Google Maps Platform** - Maps Integration
3. **Firebase Cloud Messaging** - Push Notifications
4. **Hive** - Local Storage
5. **Connectivity Plus** - Network Detection

---

## 🤝 المساهمة

لتحسين هذه الميزات:

1. Fork المشروع
2. إنشاء branch جديد
3. إضافة التحسينات
4. إنشاء Pull Request

---

**صُنع بـ ❤️ في اليمن 🇾🇪**
