"""
Smoke Tests - اختبارات التحقق السريع
اختبارات سريعة للتأكد من أن النظام يعمل بشكل أساسي
"""
import sys
import os

# إضافة المسار إلى PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """اختبار أن جميع الوحدات الأساسية قابلة للاستيراد"""
    print("🔍 اختبار الاستيراد...")
    
    try:
        import django
        print("✅ Django")
        
        from django.conf import settings
        print("✅ Django Settings")
        
        from rest_framework import viewsets
        print("✅ Django REST Framework")
        
        from users.models import User
        print("✅ Users Models")
        
        from farms.models import Farm, Crop, Field
        print("✅ Farms Models")
        
        from iot.models import IoTDevice, Sensor, Actuator
        print("✅ IoT Models")
        
        from ai.disease_detection import PlantDiseaseDetector
        print("✅ AI Disease Detection")
        
        from satellite.sentinel_api import SentinelAnalyzer
        print("✅ Satellite API")
        
        from irrigation.smart_controller import SmartIrrigationController
        print("✅ Smart Irrigation")
        
        from marketplace.models import CropListing, Offer
        print("✅ Marketplace Models")
        
        print("\n✅ جميع الوحدات قابلة للاستيراد\n")
        return True
        
    except ImportError as e:
        print(f"\n❌ فشل الاستيراد: {e}\n")
        return False


def test_database_connection():
    """اختبار الاتصال بقاعدة البيانات"""
    print("🔍 اختبار الاتصال بقاعدة البيانات...")
    
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()
        
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        if result:
            print("✅ الاتصال بقاعدة البيانات يعمل\n")
            return True
        else:
            print("❌ فشل الاتصال بقاعدة البيانات\n")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}\n")
        return False


def test_models_basic():
    """اختبار إنشاء كائنات أساسية من النماذج"""
    print("🔍 اختبار النماذج الأساسية...")
    
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()
        
        from users.models import User
        from farms.models import Farm
        
        # محاولة إنشاء مستخدم (في الذاكرة فقط)
        user = User(
            username='test_smoke',
            email='smoke@test.com',
            user_type='farmer'
        )
        print(f"✅ User Model: {user.username}")
        
        # محاولة إنشاء مزرعة (في الذاكرة فقط)
        farm = Farm(
            name='مزرعة الاختبار',
            location='صنعاء',
            area=10.0,
            soil_type='loamy'
        )
        print(f"✅ Farm Model: {farm.name}")
        
        print("\n✅ النماذج الأساسية تعمل\n")
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ في النماذج: {e}\n")
        return False


def test_api_endpoints_exist():
    """اختبار أن endpoints الأساسية موجودة"""
    print("🔍 اختبار وجود API Endpoints...")
    
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()
        
        from django.urls import resolve, reverse
        
        # قائمة endpoints الأساسية
        endpoints = [
            '/api/users/',
            '/api/farms/',
            '/api/crops/',
            '/api/fields/',
            '/api/iot-devices/',
            '/api/sensors/',
            '/api/actuators/',
        ]
        
        for endpoint in endpoints:
            try:
                resolve(endpoint)
                print(f"✅ {endpoint}")
            except:
                print(f"❌ {endpoint} - غير موجود")
                return False
        
        print("\n✅ جميع Endpoints الأساسية موجودة\n")
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ في فحص Endpoints: {e}\n")
        return False


def test_ai_modules():
    """اختبار وحدات الذكاء الاصطناعي"""
    print("🔍 اختبار وحدات الذكاء الاصطناعي...")
    
    try:
        from ai.disease_detection import PlantDiseaseDetector
        
        detector = PlantDiseaseDetector()
        diseases = detector.get_supported_diseases()
        
        if len(diseases) > 0:
            print(f"✅ Disease Detector: {len(diseases)} أمراض مدعومة")
        else:
            print("⚠️  Disease Detector: لا توجد أمراض مدعومة")
        
        print("\n✅ وحدات AI تعمل\n")
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ في وحدات AI: {e}\n")
        return False


def test_satellite_module():
    """اختبار وحدة الأقمار الصناعية"""
    print("🔍 اختبار وحدة الأقمار الصناعية...")
    
    try:
        from satellite.sentinel_api import SentinelAnalyzer
        
        analyzer = SentinelAnalyzer()
        print("✅ Sentinel Analyzer")
        
        print("\n✅ وحدة الأقمار الصناعية تعمل\n")
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ في وحدة الأقمار: {e}\n")
        return False


def test_irrigation_module():
    """اختبار وحدة الري الذكي"""
    print("🔍 اختبار وحدة الري الذكي...")
    
    try:
        from irrigation.smart_controller import SmartIrrigationController
        
        controller = SmartIrrigationController()
        print("✅ Smart Irrigation Controller")
        
        print("\n✅ وحدة الري الذكي تعمل\n")
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ في وحدة الري: {e}\n")
        return False


def run_all_smoke_tests():
    """تشغيل جميع اختبارات Smoke"""
    print("=" * 60)
    print("🚀 بدء Smoke Tests")
    print("=" * 60)
    print()
    
    results = {
        'الاستيراد': test_imports(),
        'قاعدة البيانات': test_database_connection(),
        'النماذج الأساسية': test_models_basic(),
        'API Endpoints': test_api_endpoints_exist(),
        'وحدات AI': test_ai_modules(),
        'الأقمار الصناعية': test_satellite_module(),
        'الري الذكي': test_irrigation_module(),
    }
    
    print("=" * 60)
    print("📊 ملخص النتائج")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ نجح" if result else "❌ فشل"
        print(f"{test_name}: {status}")
    
    print()
    print(f"النتيجة النهائية: {passed}/{total} اختبارات نجحت")
    print("=" * 60)
    
    return all(results.values())


if __name__ == '__main__':
    success = run_all_smoke_tests()
    sys.exit(0 if success else 1)
