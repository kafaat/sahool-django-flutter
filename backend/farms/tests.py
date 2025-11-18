"""
Unit Tests لتطبيق المزارع
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from farms.models import Farm, Crop, Field, IrrigationSchedule
from datetime import date, timedelta

User = get_user_model()


class FarmModelTest(TestCase):
    """اختبارات نموذج المزرعة"""
    
    def setUp(self):
        """إعداد بيانات الاختبار"""
        self.user = User.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='testpass123',
            user_type='farmer'
        )
        
        self.farm = Farm.objects.create(
            owner=self.user,
            name='مزرعة الاختبار',
            location='صنعاء، اليمن',
            area=10.5,
            soil_type='loamy',
            latitude=15.3694,
            longitude=44.1910
        )
    
    def test_farm_creation(self):
        """اختبار إنشاء مزرعة"""
        self.assertEqual(self.farm.name, 'مزرعة الاختبار')
        self.assertEqual(self.farm.owner, self.user)
        self.assertEqual(self.farm.area, 10.5)
        self.assertEqual(self.farm.soil_type, 'loamy')
    
    def test_farm_str(self):
        """اختبار __str__ للمزرعة"""
        expected = f"{self.farm.name} - {self.user.username}"
        self.assertEqual(str(self.farm), expected)
    
    def test_farm_latitude_longitude(self):
        """اختبار إحداثيات GPS"""
        self.assertIsNotNone(self.farm.latitude)
        self.assertIsNotNone(self.farm.longitude)
        self.assertEqual(float(self.farm.latitude), 15.3694)
        self.assertEqual(float(self.farm.longitude), 44.1910)


class CropModelTest(TestCase):
    """اختبارات نموذج المحصول"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='testpass123'
        )
        
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
            area=2.5,
            status='growing'
        )
    
    def test_crop_creation(self):
        """اختبار إنشاء محصول"""
        self.assertEqual(self.crop.name, 'طماطم')
        self.assertEqual(self.crop.variety, 'روما')
        self.assertEqual(self.crop.farm, self.farm)
        self.assertEqual(self.crop.status, 'growing')
    
    def test_crop_str(self):
        """اختبار __str__ للمحصول"""
        expected = f"{self.crop.name} ({self.crop.variety}) - {self.farm.name}"
        self.assertEqual(str(self.crop), expected)
    
    def test_crop_dates(self):
        """اختبار تواريخ الزراعة والحصاد"""
        self.assertIsNotNone(self.crop.planting_date)
        self.assertIsNotNone(self.crop.expected_harvest_date)
        self.assertGreater(
            self.crop.expected_harvest_date,
            self.crop.planting_date
        )


class FieldModelTest(TestCase):
    """اختبارات نموذج الحقل"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='testpass123'
        )
        
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
            soil_ph=6.5,
            health_status='healthy'
        )
    
    def test_field_creation(self):
        """اختبار إنشاء حقل"""
        self.assertEqual(self.field.name, 'حقل رقم 1')
        self.assertEqual(self.field.farm, self.farm)
        self.assertEqual(self.field.crop, self.crop)
        self.assertEqual(self.field.health_status, 'healthy')
    
    def test_field_soil_properties(self):
        """اختبار خصائص التربة"""
        self.assertEqual(float(self.field.soil_moisture), 0.25)
        self.assertEqual(float(self.field.soil_ph), 6.5)
        self.assertGreaterEqual(float(self.field.soil_moisture), 0.0)
        self.assertLessEqual(float(self.field.soil_moisture), 1.0)
    
    def test_field_str(self):
        """اختبار __str__ للحقل"""
        expected = f"{self.field.name} - {self.farm.name}"
        self.assertEqual(str(self.field), expected)


class IrrigationScheduleTest(TestCase):
    """اختبارات جدول الري"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='testpass123'
        )
        
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
            area=2.5
        )
        
        self.schedule = IrrigationSchedule.objects.create(
            field=self.field,
            scheduled_date=date.today() + timedelta(days=1),
            duration_minutes=60,
            water_amount=100.0,
            method='drip',
            status='pending'
        )
    
    def test_schedule_creation(self):
        """اختبار إنشاء جدول ري"""
        self.assertEqual(self.schedule.field, self.field)
        self.assertEqual(self.schedule.duration_minutes, 60)
        self.assertEqual(float(self.schedule.water_amount), 100.0)
        self.assertEqual(self.schedule.method, 'drip')
        self.assertEqual(self.schedule.status, 'pending')
    
    def test_schedule_str(self):
        """اختبار __str__ لجدول الري"""
        expected = f"ري {self.field.name} - {self.schedule.scheduled_date}"
        self.assertEqual(str(self.schedule), expected)
    
    def test_schedule_status_change(self):
        """اختبار تغيير حالة الجدول"""
        self.schedule.status = 'completed'
        self.schedule.save()
        self.assertEqual(self.schedule.status, 'completed')
