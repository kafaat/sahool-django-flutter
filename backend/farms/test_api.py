"""
API Tests لتطبيق المزارع
"""
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from farms.models import Farm, Crop, Field
from datetime import date, timedelta

User = get_user_model()


class FarmAPITest(APITestCase):
    """اختبارات API المزارع"""
    
    def setUp(self):
        """إعداد بيانات الاختبار"""
        self.client = APIClient()
        
        # إنشاء مستخدم
        self.user = User.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='testpass123',
            user_type='farmer'
        )
        
        # تسجيل الدخول
        self.client.force_authenticate(user=self.user)
        
        # إنشاء مزرعة
        self.farm = Farm.objects.create(
            owner=self.user,
            name='مزرعة الاختبار',
            location='صنعاء، اليمن',
            area=10.5,
            soil_type='loamy'
        )
    
    def test_get_farms_list(self):
        """اختبار الحصول على قائمة المزارع"""
        response = self.client.get('/api/farms/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_get_farm_detail(self):
        """اختبار الحصول على تفاصيل مزرعة"""
        response = self.client.get(f'/api/farms/{self.farm.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'مزرعة الاختبار')
    
    def test_create_farm(self):
        """اختبار إنشاء مزرعة جديدة"""
        data = {
            'name': 'مزرعة جديدة',
            'location': 'تعز، اليمن',
            'area': 15.0,
            'soil_type': 'sandy'
        }
        response = self.client.post('/api/farms/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'مزرعة جديدة')
    
    def test_update_farm(self):
        """اختبار تحديث مزرعة"""
        data = {
            'name': 'مزرعة محدثة',
            'location': self.farm.location,
            'area': 12.0,
            'soil_type': self.farm.soil_type
        }
        response = self.client.put(f'/api/farms/{self.farm.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'مزرعة محدثة')
        self.assertEqual(float(response.data['area']), 12.0)
    
    def test_delete_farm(self):
        """اختبار حذف مزرعة"""
        response = self.client.delete(f'/api/farms/{self.farm.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # التحقق من الحذف
        response = self.client.get(f'/api/farms/{self.farm.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_farm_statistics(self):
        """اختبار الحصول على إحصائيات المزرعة"""
        response = self.client.get(f'/api/farms/{self.farm.id}/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_area', response.data)


class CropAPITest(APITestCase):
    """اختبارات API المحاصيل"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=self.user)
        
        self.farm = Farm.objects.create(
            owner=self.user,
            name='مزرعة الاختبار',
            location='صنعاء',
            area=10.0,
            soil_type='loamy'
        )
        
        self.crop = Crop.objects.create(
            farm=self.farm,
            name='طماطم',
            variety='روما',
            planting_date=date.today(),
            expected_harvest_date=date.today() + timedelta(days=90),
            area=2.5
        )
    
    def test_get_crops_list(self):
        """اختبار الحصول على قائمة المحاصيل"""
        response = self.client.get('/api/crops/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_crop(self):
        """اختبار إنشاء محصول جديد"""
        data = {
            'farm': self.farm.id,
            'name': 'خيار',
            'variety': 'أخضر',
            'planting_date': date.today().isoformat(),
            'expected_harvest_date': (date.today() + timedelta(days=60)).isoformat(),
            'area': 1.5
        }
        response = self.client.post('/api/crops/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'خيار')
    
    def test_update_crop_status(self):
        """اختبار تحديث حالة المحصول"""
        data = {
            'farm': self.farm.id,
            'name': self.crop.name,
            'variety': self.crop.variety,
            'planting_date': self.crop.planting_date.isoformat(),
            'expected_harvest_date': self.crop.expected_harvest_date.isoformat(),
            'area': self.crop.area,
            'status': 'harvested'
        }
        response = self.client.put(f'/api/crops/{self.crop.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'harvested')


class FieldAPITest(APITestCase):
    """اختبارات API الحقول"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=self.user)
        
        self.farm = Farm.objects.create(
            owner=self.user,
            name='مزرعة الاختبار',
            location='صنعاء',
            area=10.0,
            soil_type='loamy'
        )
        
        self.crop = Crop.objects.create(
            farm=self.farm,
            name='طماطم',
            planting_date=date.today(),
            expected_harvest_date=date.today() + timedelta(days=90),
            area=2.5
        )
        
        self.field = Field.objects.create(
            farm=self.farm,
            crop=self.crop,
            name='حقل رقم 1',
            area=2.5,
            soil_moisture=0.25,
            soil_ph=6.5
        )
    
    def test_get_fields_list(self):
        """اختبار الحصول على قائمة الحقول"""
        response = self.client.get('/api/fields/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_field(self):
        """اختبار إنشاء حقل جديد"""
        data = {
            'farm': self.farm.id,
            'crop': self.crop.id,
            'name': 'حقل رقم 2',
            'area': 3.0,
            'soil_moisture': 0.30,
            'soil_ph': 6.8
        }
        response = self.client.post('/api/fields/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'حقل رقم 2')
    
    def test_get_field_health_status(self):
        """اختبار الحصول على حالة صحة الحقل"""
        response = self.client.get(f'/api/fields/{self.field.id}/health_status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('health_status', response.data)


class AuthenticationTest(APITestCase):
    """اختبارات المصادقة"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_login_required(self):
        """اختبار أن APIs تتطلب تسجيل دخول"""
        response = self.client.get('/api/farms/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_access(self):
        """اختبار الوصول بعد المصادقة"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/farms/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
