# 🧪 دليل الاختبارات - منصة سهول

## 📋 نظرة عامة

تم إضافة مجموعة شاملة من الاختبارات لضمان جودة المشروع:

1. **Unit Tests** - اختبارات الوحدات للنماذج
2. **API Tests** - اختبارات API Endpoints
3. **Smoke Tests** - اختبارات التحقق السريع

---

## 🎯 الاختبارات المتوفرة

### 1. Unit Tests للـ Backend (Django)

**الملف**: `backend/farms/tests.py`

#### الاختبارات المتضمنة:

##### FarmModelTest
- `test_farm_creation` - إنشاء مزرعة
- `test_farm_str` - تمثيل نصي للمزرعة
- `test_farm_latitude_longitude` - إحداثيات GPS

##### CropModelTest
- `test_crop_creation` - إنشاء محصول
- `test_crop_str` - تمثيل نصي للمحصول
- `test_crop_dates` - تواريخ الزراعة والحصاد

##### FieldModelTest
- `test_field_creation` - إنشاء حقل
- `test_field_soil_properties` - خصائص التربة
- `test_field_str` - تمثيل نصي للحقل

##### IrrigationScheduleTest
- `test_schedule_creation` - إنشاء جدول ري
- `test_schedule_str` - تمثيل نصي للجدول
- `test_schedule_status_change` - تغيير حالة الجدول

#### تشغيل Unit Tests:

```bash
cd backend
python manage.py test farms.tests
```

---

### 2. API Tests للـ Endpoints

**الملف**: `backend/farms/test_api.py`

#### الاختبارات المتضمنة:

##### FarmAPITest
- `test_get_farms_list` - GET /api/farms/
- `test_get_farm_detail` - GET /api/farms/{id}/
- `test_create_farm` - POST /api/farms/
- `test_update_farm` - PUT /api/farms/{id}/
- `test_delete_farm` - DELETE /api/farms/{id}/
- `test_get_farm_statistics` - GET /api/farms/{id}/statistics/

##### CropAPITest
- `test_get_crops_list` - GET /api/crops/
- `test_create_crop` - POST /api/crops/
- `test_update_crop_status` - PUT /api/crops/{id}/

##### FieldAPITest
- `test_get_fields_list` - GET /api/fields/
- `test_create_field` - POST /api/fields/
- `test_get_field_health_status` - GET /api/fields/{id}/health_status/

##### AuthenticationTest
- `test_login_required` - التحقق من المصادقة المطلوبة
- `test_authenticated_access` - الوصول بعد المصادقة

#### تشغيل API Tests:

```bash
cd backend
python manage.py test farms.test_api
```

---

### 3. Smoke Tests - اختبارات التحقق السريع

**الملف**: `backend/smoke_tests.py`

#### الاختبارات المتضمنة:

1. **test_imports** - فحص استيراد الوحدات
2. **test_database_connection** - فحص الاتصال بقاعدة البيانات
3. **test_models_basic** - فحص النماذج الأساسية
4. **test_api_endpoints_exist** - فحص وجود Endpoints
5. **test_ai_modules** - فحص وحدات AI
6. **test_satellite_module** - فحص وحدة الأقمار
7. **test_irrigation_module** - فحص وحدة الري

#### تشغيل Smoke Tests:

```bash
cd backend
python smoke_tests.py
```

---

## 🚀 تشغيل جميع الاختبارات

### Backend (Django)

```bash
cd backend

# تشغيل جميع الاختبارات
python manage.py test

# تشغيل اختبارات تطبيق معين
python manage.py test farms

# تشغيل اختبار محدد
python manage.py test farms.tests.FarmModelTest.test_farm_creation

# مع تقرير التغطية
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Smoke Tests

```bash
cd backend
python smoke_tests.py
```

---

## 📊 تقرير التغطية (Coverage)

### تثبيت coverage:

```bash
pip install coverage
```

### تشغيل مع coverage:

```bash
cd backend

# تشغيل الاختبارات مع قياس التغطية
coverage run --source='.' manage.py test

# عرض التقرير في Terminal
coverage report

# إنشاء تقرير HTML
coverage html

# فتح التقرير
# التقرير سيكون في: htmlcov/index.html
```

---

## ✅ قائمة التحقق

### قبل الإطلاق:

- [ ] جميع Unit Tests تنجح
- [ ] جميع API Tests تنجح
- [ ] Smoke Tests تنجح
- [ ] تغطية الكود > 80%
- [ ] لا توجد أخطاء في linting
- [ ] التوثيق محدث

---

## 🐛 استكشاف الأخطاء

### مشكلة: Django not installed

```bash
cd backend
pip install -r requirements.txt
```

### مشكلة: Database connection error

```bash
# التأكد من تشغيل PostgreSQL
# أو استخدام SQLite للاختبار

# في settings.py:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### مشكلة: Import errors

```bash
# التأكد من PYTHONPATH
export PYTHONPATH=/home/ubuntu/sahool-django-flutter/backend:$PYTHONPATH

# أو تشغيل من مجلد backend
cd backend
python manage.py test
```

---

## 📝 إضافة اختبارات جديدة

### مثال: اختبار نموذج جديد

```python
# في backend/app_name/tests.py

from django.test import TestCase
from .models import YourModel

class YourModelTest(TestCase):
    def setUp(self):
        """إعداد بيانات الاختبار"""
        self.obj = YourModel.objects.create(
            field1='value1',
            field2='value2'
        )
    
    def test_creation(self):
        """اختبار إنشاء الكائن"""
        self.assertEqual(self.obj.field1, 'value1')
    
    def test_str(self):
        """اختبار __str__"""
        self.assertEqual(str(self.obj), 'expected_string')
```

### مثال: اختبار API

```python
# في backend/app_name/test_api.py

from rest_framework.test import APITestCase
from rest_framework import status

class YourAPITest(APITestCase):
    def setUp(self):
        """إعداد بيانات الاختبار"""
        self.client.force_authenticate(user=self.user)
    
    def test_get_list(self):
        """اختبار GET list"""
        response = self.client.get('/api/your-endpoint/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create(self):
        """اختبار POST create"""
        data = {'field': 'value'}
        response = self.client.post('/api/your-endpoint/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
```

---

## 🎯 أفضل الممارسات

### 1. تسمية الاختبارات
- استخدم أسماء وصفية: `test_create_farm_with_valid_data`
- ابدأ دائماً بـ `test_`

### 2. هيكلة الاختبارات
- استخدم `setUp()` للإعداد المشترك
- استخدم `tearDown()` للتنظيف إذا لزم الأمر

### 3. الاستقلالية
- كل اختبار يجب أن يكون مستقلاً
- لا تعتمد على ترتيب التنفيذ

### 4. الوضوح
- اختبار واحد لكل سيناريو
- رسائل خطأ واضحة

### 5. السرعة
- استخدم `setUpTestData()` للبيانات الثابتة
- تجنب العمليات البطيئة

---

## 📈 إحصائيات الاختبارات

### Backend Tests

| النوع | العدد | الحالة |
|-------|-------|--------|
| Unit Tests | 12 | ✅ |
| API Tests | 12 | ✅ |
| Smoke Tests | 7 | ⚠️ |
| **المجموع** | **31** | - |

### التغطية المتوقعة

| الوحدة | التغطية |
|--------|----------|
| Models | 90%+ |
| Views | 80%+ |
| Serializers | 85%+ |
| Utils | 75%+ |

---

## 🔄 التكامل المستمر (CI)

### GitHub Actions (مقترح)

```yaml
# .github/workflows/tests.yml

name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd backend
        python manage.py test
    
    - name: Run smoke tests
      run: |
        cd backend
        python smoke_tests.py
```

---

## 📚 المراجع

1. **Django Testing** - https://docs.djangoproject.com/en/stable/topics/testing/
2. **Django REST Framework Testing** - https://www.django-rest-framework.org/api-guide/testing/
3. **Coverage.py** - https://coverage.readthedocs.io/
4. **Python unittest** - https://docs.python.org/3/library/unittest.html

---

## ✨ الخلاصة

تم إنشاء مجموعة شاملة من الاختبارات تغطي:

✅ **31 اختبار** للـ Backend
✅ **Unit Tests** للنماذج
✅ **API Tests** للـ Endpoints
✅ **Smoke Tests** للتحقق السريع
✅ **توثيق كامل** لكيفية التشغيل

**الاختبارات جاهزة للاستخدام! 🎉**

---

**صُنع بـ ❤️ في اليمن 🇾🇪**
