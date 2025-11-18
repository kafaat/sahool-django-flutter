# دليل الإعداد والتشغيل - Sahool Smart Agriculture Platform

## المحتويات
1. [المتطلبات الأساسية](#المتطلبات-الأساسية)
2. [إعداد Backend Django](#إعداد-backend-django)
3. [إعداد Mobile Flutter](#إعداد-mobile-flutter)
4. [التشغيل باستخدام Docker](#التشغيل-باستخدام-docker)
5. [اختبار API](#اختبار-api)
6. [حل المشاكل الشائعة](#حل-المشاكل-الشائعة)

---

## المتطلبات الأساسية

### للتطوير المحلي:
- **Python**: 3.10 أو أحدث
- **PostgreSQL**: 13 أو أحدث
- **Redis**: 6 أو أحدث
- **Flutter**: 3.0 أو أحدث
- **Git**: لإدارة الإصدارات

### للتشغيل باستخدام Docker:
- **Docker**: 20.10 أو أحدث
- **Docker Compose**: 2.0 أو أحدث

---

## إعداد Backend Django

### 1. استنساخ المشروع
```bash
git clone https://github.com/kafaat/sahool-django-flutter.git
cd sahool-django-flutter/backend
```

### 2. إنشاء بيئة افتراضية
```bash
# على Linux/Mac
python3 -m venv venv
source venv/bin/activate

# على Windows
python -m venv venv
venv\Scripts\activate
```

### 3. تثبيت التبعيات
```bash
pip install -r requirements.txt
```

### 4. إعداد قاعدة البيانات PostgreSQL

#### على Linux/Mac:
```bash
# تثبيت PostgreSQL
sudo apt-get install postgresql postgresql-contrib  # Ubuntu/Debian
# أو
brew install postgresql  # macOS

# إنشاء قاعدة بيانات
sudo -u postgres psql
CREATE DATABASE sahool_db;
CREATE USER sahool_user WITH PASSWORD 'sahool_password';
ALTER ROLE sahool_user SET client_encoding TO 'utf8';
ALTER ROLE sahool_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE sahool_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE sahool_db TO sahool_user;
\q
```

#### على Windows:
1. قم بتنزيل وتثبيت PostgreSQL من الموقع الرسمي
2. استخدم pgAdmin لإنشاء قاعدة البيانات والمستخدم

### 5. إعداد Redis

#### على Linux:
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

#### على macOS:
```bash
brew install redis
brew services start redis
```

#### على Windows:
قم بتنزيل Redis من GitHub وتشغيله

### 6. إنشاء ملف المتغيرات البيئية
```bash
# في مجلد backend
cat > .env << EOF
SECRET_KEY=django-insecure-change-this-in-production-$(openssl rand -hex 32)
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=sahool_db
POSTGRES_USER=sahool_user
POSTGRES_PASSWORD=sahool_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/1
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
EOF
```

### 7. تطبيق الهجرات
```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. إنشاء مستخدم مدير
```bash
python manage.py createsuperuser
```

### 9. تشغيل الخادم
```bash
# في نافذة طرفية منفصلة
python manage.py runserver

# في نافذة أخرى - تشغيل Celery (اختياري)
celery -A config worker -l info
```

### 10. التحقق من التثبيت
افتح المتصفح وانتقل إلى:
- **Admin Panel**: http://localhost:8000/admin/
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

---

## إعداد Mobile Flutter

### 1. تثبيت Flutter
```bash
# على Linux/Mac
git clone https://github.com/flutter/flutter.git -b stable
export PATH="$PATH:`pwd`/flutter/bin"

# على Windows - قم بتنزيل Flutter SDK من الموقع الرسمي
```

### 2. التحقق من التثبيت
```bash
flutter doctor
```

### 3. الانتقال إلى مجلد Mobile
```bash
cd sahool-django-flutter/mobile
```

### 4. تثبيت التبعيات
```bash
flutter pub get
```

### 5. تشغيل Code Generation
```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

### 6. تحديث عنوان API
افتح `lib/utils/constants.dart` وقم بتحديث:
```dart
static const String baseUrl = 'http://YOUR_IP:8000/api';
static const String authUrl = 'http://YOUR_IP:8000/api/auth';
```

**ملاحظة**: استخدم عنوان IP الفعلي لجهازك بدلاً من `localhost` عند التشغيل على جهاز فعلي.

### 7. تشغيل التطبيق

#### على محاكي Android:
```bash
# تشغيل محاكي
flutter emulators --launch <emulator_id>

# تشغيل التطبيق
flutter run
```

#### على جهاز فعلي:
1. قم بتفعيل وضع المطور على الجهاز
2. قم بتوصيل الجهاز عبر USB
3. قم بتفعيل USB Debugging
4. شغل التطبيق:
```bash
flutter run
```

#### على iOS (macOS فقط):
```bash
# فتح المشروع في Xcode
open ios/Runner.xcworkspace

# أو التشغيل مباشرة
flutter run
```

---

## التشغيل باستخدام Docker

### 1. تثبيت Docker و Docker Compose
راجع الموقع الرسمي لـ Docker للحصول على تعليمات التثبيت.

### 2. إنشاء ملف .env
```bash
# في المجلد الرئيسي
cp backend/.env.example .env
# قم بتحرير .env حسب الحاجة
```

### 3. بناء وتشغيل الحاويات
```bash
# بناء الصور
docker-compose build

# تشغيل الخدمات
docker-compose up -d

# عرض السجلات
docker-compose logs -f
```

### 4. تطبيق الهجرات
```bash
docker-compose exec backend python manage.py migrate
```

### 5. إنشاء مستخدم مدير
```bash
docker-compose exec backend python manage.py createsuperuser
```

### 6. الوصول إلى الخدمات
- **Django Backend**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 7. إيقاف الخدمات
```bash
docker-compose down

# لحذف البيانات أيضاً
docker-compose down -v
```

---

## اختبار API

### 1. باستخدام Swagger UI
1. افتح http://localhost:8000/swagger/
2. انقر على "Authorize" وأدخل التوكن
3. جرب الـ endpoints المختلفة

### 2. باستخدام cURL

#### تسجيل مستخدم جديد:
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "farmer1",
    "email": "farmer1@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "user_type": "farmer",
    "first_name": "أحمد",
    "last_name": "محمد"
  }'
```

#### تسجيل الدخول:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "farmer1",
    "password": "password123"
  }'
```

#### الحصول على قائمة المزارع:
```bash
curl -X GET http://localhost:8000/api/farms/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. باستخدام Postman
1. استورد مجموعة Postman من ملف `docs/postman_collection.json`
2. قم بتعيين متغير البيئة `base_url` إلى `http://localhost:8000`
3. سجل الدخول واحصل على التوكن
4. استخدم التوكن في الطلبات الأخرى

---

## حل المشاكل الشائعة

### مشكلة: خطأ في الاتصال بقاعدة البيانات
**الحل:**
```bash
# تحقق من أن PostgreSQL يعمل
sudo systemctl status postgresql

# تحقق من بيانات الاعتماد في .env
cat .env | grep POSTGRES

# أعد تشغيل PostgreSQL
sudo systemctl restart postgresql
```

### مشكلة: خطأ في الاتصال بـ Redis
**الحل:**
```bash
# تحقق من أن Redis يعمل
redis-cli ping
# يجب أن يرجع: PONG

# أعد تشغيل Redis
sudo systemctl restart redis-server
```

### مشكلة: Flutter لا يجد الأجهزة
**الحل:**
```bash
# تحقق من الأجهزة المتصلة
flutter devices

# أعد تشغيل adb (لـ Android)
adb kill-server
adb start-server
```

### مشكلة: خطأ في Code Generation
**الحل:**
```bash
# احذف الملفات المولدة وأعد التوليد
flutter clean
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

### مشكلة: التطبيق لا يتصل بـ API
**الحل:**
1. تأكد من أن Backend يعمل
2. تحقق من عنوان IP في `constants.dart`
3. على Android، استخدم `10.0.2.2` للوصول إلى localhost على الجهاز المضيف
4. على iOS، استخدم عنوان IP الفعلي للجهاز

### مشكلة: CORS Error
**الحل:**
أضف عنوان التطبيق إلى `CORS_ALLOWED_ORIGINS` في `.env`:
```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://10.0.2.2:8000
```

---

## الخطوات التالية

بعد الإعداد الناجح:

1. **استكشف الـ API**: استخدم Swagger UI لاستكشاف جميع الـ endpoints
2. **أضف بيانات تجريبية**: أنشئ مزارع وحقول وأجهزة IoT
3. **اختبر التطبيق المحمول**: جرب جميع الميزات على التطبيق
4. **طور ميزات جديدة**: راجع TODO.md للميزات المخطط لها
5. **ساهم في المشروع**: راجع CONTRIBUTING.md (إن وجد)

---

## الدعم

إذا واجهت أي مشاكل:
- افتح Issue على GitHub
- راسلنا على support@sahool.com
- راجع التوثيق الكامل في مجلد `docs/`

---

**صُنع بـ ❤️ في اليمن**
