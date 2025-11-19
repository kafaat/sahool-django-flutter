"""
نماذج الأقمار الصناعية - التكامل الشامل
Satellite Models - Comprehensive Integration
"""

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.postgres.fields import JSONField

from apps.core.models import BaseModel
from apps.farms.models import Farm, Crop, Field

User = get_user_model()


class SatelliteData(BaseModel):
    """نموذج بيانات الأقمار الصناعية"""
    
    SATELLITE_SOURCES = [
        ('sentinel2', 'Sentinel-2'),
        ('landsat8', 'Landsat-8'),
        ('landsat9', 'Landsat-9'),
        ('modis', 'MODIS'),
        ('planet', 'Planet'),
        ('sentinel1', 'Sentinel-1'),
    ]
    
    DATA_TYPES = [
        ('optical', 'بصري'),
        ('radar', 'رادار'),
        ('thermal', 'حراري'),
        ('multispectral', 'متعدد الطيف'),
        ('hyperspectral', 'فائق الطيف'),
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='satellite_data', verbose_name='المزرعة')
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='satellite_data', verbose_name='الحقل')
    
    # مصدر البيانات
    satellite_source = models.CharField(max_length=20, choices=SATELLITE_SOURCES, verbose_name='مصدر القمر الصناعي')
    data_type = models.CharField(max_length=20, choices=DATA_TYPES, verbose_name='نوع البيانات')
    
    # تواريخ التقاط
    acquisition_date = models.DateField(verbose_name='تاريخ التقاط الصورة')
    acquisition_time = models.TimeField(verbose_name='وقت التقاط الصورة')
    
    # الموقع الجغرافي
    tile_id = models.CharField(max_length=20, verbose_name='معرف البلاطة')
    footprint = gis_models.PolygonField(geography=True, verbose_name='نطاق التغطية')
    center_coordinates = gis_models.PointField(geography=True, verbose_name='إحداثيات المركز')
    
    # البيانات الأساسية
    image_url = models.URLField(verbose_name='رابط الصورة')
    thumbnail_url = models.URLField(blank=True, verbose_name='رابط الصورة المصغرة')
    cloud_cover_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='نسبة الغيوم (%)')
    
    # جودة الصورة
    image_quality = models.CharField(max_length=20, choices=[
        ('excellent', 'ممتاز'),
        ('good', 'جيد'),
        ('fair', 'مقبول'),
        ('poor', 'ضعيف'),
    ], verbose_name='جودة الصورة')
    
    # المعلومات التقنية
    resolution_meters = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='الدقة (متر)')
    bands_count = models.PositiveIntegerField(verbose_name='عدد الحزم الطيفية')
    bands_info = JSONField(default=dict, verbose_name='معلومات الحزم الطيفية')
    
    # معالجة الصور
    is_processed = models.BooleanField(default=False, verbose_name='تمت المعالجة')
    processing_date = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ المعالجة')
    processing_method = models.CharField(max_length=50, blank=True, verbose_name='طريقة المعالجة')
    
    # التخزين
    file_size_mb = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='حجم الملف (ميجابايت)')
    storage_path = models.CharField(max_length=500, verbose_name='مسار التخزين')
    
    # التحقق
    is_validated = models.BooleanField(default=False, verbose_name='تم التحقق')
    validation_date = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ التحقق')
    validation_notes = models.TextField(blank=True, verbose_name='ملاحظات التحقق')
    
    class Meta:
        db_table = 'satellite_data'
        verbose_name = 'بيانات قمر صناعي'
        verbose_name_plural = 'بيانات الأقمار الصناعية'
        ordering = ['-acquisition_date', '-acquisition_time']
        indexes = [
            models.Index(fields=['farm', 'acquisition_date']),
            models.Index(fields=['satellite_source', 'acquisition_date']),
            models.Index(fields=['tile_id', 'acquisition_date']),
            models.Index(fields=['center_coordinates']),
        ]
    
    def __str__(self):
        return f"{self.get_satellite_source_display()} - {self.acquisition_date} - {self.farm.name}"
    
    def mark_as_processed(self, processing_method):
        """وضع علامة كمُعالَج"""
        self.is_processed = True
        self.processing_date = timezone.now()
        self.processing_method = processing_method
        self.save(update_fields=['is_processed', 'processing_date', 'processing_method'])
    
    def mark_as_validated(self, notes=None):
        """وضع علامة كمُحقَّق"""
        self.is_validated = True
        self.validation_date = timezone.now()
        if notes:
            self.validation_notes = notes
        self.save(update_fields=['is_validated', 'validation_date', 'validation_notes'])


class NDVIAnalysis(BaseModel):
    """نموذج تحليل مؤشر NDVI"""
    
    satellite_data = models.OneToOneField(SatelliteData, on_delete=models.CASCADE, related_name='ndvi_analysis', verbose_name='بيانات القمر الصناعي')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='ndvi_analyses', verbose_name='المزرعة')
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='ndvi_analyses', verbose_name='الحقل')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='ndvi_analyses', verbose_name='المحصول', null=True, blank=True)
    
    # قيم NDVI
    ndvi_value = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(-1), MaxValueValidator(1)], verbose_name='قيمة NDVI')
    ndvi_min = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(-1), MaxValueValidator(1)], verbose_name='أقل قيمة NDVI')
    ndvi_max = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(-1), MaxValueValidator(1)], verbose_name='أعلى قيمة NDVI')
    ndvi_mean = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(-1), MaxValueValidator(1)], verbose_name='متوسط NDVI')
    ndvi_std = models.DecimalField(max_digits=6, decimal_places=4, verbose_name='الانحراف المعياري لـ NDVI')
    
    # التفسير
    health_status = models.CharField(max_length=20, choices=[
        ('very_poor', 'سيء جداً'),
        ('poor', 'سيء'),
        ('fair', 'مقبول'),
        ('good', 'جيد'),
        ('very_good', 'جيد جداً'),
        ('excellent', 'ممتاز'),
    ], verbose_name='حالة الصحة')
    
    # التغيرات الزمنية
    ndvi_change_from_previous = models.DecimalField(max_digits=6, decimal_places=4, verbose_name='التغير عن السابق')
    ndvi_trend = models.CharField(max_length=20, choices=[
        ('improving', 'تحسن'),
        ('declining', 'تدهور'),
        ('stable', 'مستقر'),
        ('fluctuating', 'متقلب'),
    ], verbose_name='الاتجاه')
    
    # المساحة
    total_area_hectares = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='المساحة الكلية (هكتار)')
    healthy_area_hectares = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='المساحة الصحية (هكتار)')
    stressed_area_hectares = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='المساحة المتأثرة (هكتار)')
    
    # نسب المساحات
    healthy_area_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='نسبة المساحة الصحية (%)')
    stressed_area_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='نسبة المساحة المتأثرة (%)')
    
    # التوصيات
    recommendations = JSONField(default=dict, verbose_name='التوصيات')
    alerts = JSONField(default=list, verbose_name='التنبيهات')
    
    # البيانات المرئية
    ndvi_map_url = models.URLField(blank=True, verbose_name='رابط خريطة NDVI')
    ndvi_map_path = models.CharField(max_length=500, blank=True, verbose_name='مسار خريطة NDVI')
    
    # التحقق
    is_valid = models.BooleanField(default=True, verbose_name='صالح')
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='درجة الجودة')
    
    class Meta:
        db_table = 'ndvi_analyses'
        verbose_name = 'تحليل NDVI'
        verbose_name_plural = 'تحليلات NDVI'
        ordering = ['-satellite_data__acquisition_date']
        indexes = [
            models.Index(fields=['farm', 'satellite_data__acquisition_date']),
            models.Index(fields=['field', 'health_status']),
            models.Index(fields=['ndvi_value']),
        ]
    
    def __str__(self):
        return f"تحليل NDVI - {self.field.name} - {self.satellite_data.acquisition_date}"
    
    def calculate_health_status(self):
        """حساب حالة الصحة بناءً على قيمة NDVI"""
        if self.ndvi_value >= 0.8:
            self.health_status = 'excellent'
        elif self.ndvi_value >= 0.6:
            self.health_status = 'very_good'
        elif self.ndvi_value >= 0.4:
            self.health_status = 'good'
        elif self.ndvi_value >= 0.2:
            self.health_status = 'fair'
        elif self.ndvi_value >= 0.1:
            self.health_status = 'poor'
        else:
            self.health_status = 'very_poor'
        
        self.save(update_fields=['health_status'])
        return self.health_status
    
    def calculate_area_percentages(self):
        """حساب نسب المساحات"""
        if self.total_area_hectares > 0:
            self.healthy_area_percentage = (self.healthy_area_hectares / self.total_area_hectares) * 100
            self.stressed_area_percentage = (self.stressed_area_hectares / self.total_area_hectares) * 100
            self.save(update_fields=['healthy_area_percentage', 'stressed_area_percentage'])


class CropHealthAssessment(BaseModel):
    """نموذج تقييم صحة المحاصيل بالأقمار الصناعية"""
    
    satellite_data = models.ForeignKey(SatelliteData, on_delete=models.CASCADE, related_name='crop_health_assessments', verbose_name='بيانات القمر الصناعي')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='crop_health_assessments', verbose_name='المزرعة')
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='crop_health_assessments', verbose_name='الحقل')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='crop_health_assessments', verbose_name='المحصول')
    
    # مؤشرات الصحة
    overall_health_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='درجة الصحة العامة')
    
    # المؤشرات الطيفية
    ndvi = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(-1), MaxValueValidator(1)], verbose_name='NDVI')
    evi = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(-1), MaxValueValidator(1)], verbose_name='EVI', null=True, blank=True)
    savi = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(-1), MaxValueValidator(1)], verbose_name='SAVI', null=True, blank=True)
    msavi = models.DecimalField(max_digits=6, decimal_places=4, validators=[MinValueValidator(-1), MaxValueValidator(1)], verbose_name='MSAVI', null=True, blank=True)
    
    # مؤشرات الإجهاد
    stress_index = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='مؤشر الإجهاد')
    water_stress_index = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='مؤشر إجهاد الماء')
    nutrient_stress_index = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='مؤشر إجهاد العناصر الغذائية')
    
    # مرحلة النمو
    detected_growth_stage = models.CharField(max_length=50, verbose_name='مرحلة النمو المكتشفة')
    growth_stage_confidence = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='نسبة ثقة مرحلة النمو')
    
    # الكثافة والتغطية
    vegetation_density = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='كثافة النباتات (%)')
    canopy_coverage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='تغطية المظلة (%)')
    
    # التوصيات
    irrigation_recommendation = JSONField(default=dict, verbose_name='توصية الري')
    fertilization_recommendation = JSONField(default=dict, verbose_name='توصية التسميد')
    pest_management_recommendation = JSONField(default=dict, verbose_name='توصية مكافحة الآفات')
    
    # التنبيهات
    alerts = JSONField(default=list, verbose_name='التنبيهات')
    critical_alerts = JSONField(default=list, verbose_name='التنبيهات الحرجة')
    
    # المقارنة الزمنية
    previous_assessment = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='التقييم السابق')
    change_in_health = models.DecimalField(max_digits=6, decimal_places=4, verbose_name='التغير في الصحة')
    change_in_stress = models.DecimalField(max_digits=6, decimal_places=4, verbose_name='التغير في الإجهاد')
    
    # التحقق
    is_validated = models.BooleanField(default=False, verbose_name='تم التحقق')
    validation_method = models.CharField(max_length=50, blank=True, verbose_name='طريقة التحقق')
    accuracy_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='درجة الدقة')
    
    class Meta:
        db_table = 'crop_health_assessments'
        verbose_name = 'تقييم صحة محصول'
        verbose_name_plural = 'تقييمات صحة المحاصيل'
        ordering = ['-satellite_data__acquisition_date']
        indexes = [
            models.Index(fields=['farm', 'satellite_data__acquisition_date']),
            models.Index(fields=['crop', 'overall_health_score']),
            models.Index(fields=['stress_index']),
        ]
    
    def __str__(self):
        return f"تقييم صحة {self.crop.name} - {self.overall_health_score}%"
    
    def calculate_health_score(self):
        """حساب درجة الصحة العامة"""
        # حساب مركب بناءً على عدة مؤشرات
        ndvi_score = max(0, (self.ndvi + 1) / 2 * 100)  # تحويل NDVI (-1 to 1) إلى نسبة (0 to 100)
        
        # خصم نقاط للإجهاد
        stress_penalty = (self.stress_index + self.water_stress_index + self.nutrient_stress_index) / 3 * 0.3
        
        # حساب النتيجة النهائية
        self.overall_health_score = max(0, ndvi_score - stress_penalty)
        self.save(update_fields=['overall_health_score'])
        return self.overall_health_score
    
    def generate_alerts(self):
        """إنشاء التنبيهات بناءً على التقييم"""
        alerts = []
        critical_alerts = []
        
        if self.water_stress_index > 70:
            critical_alerts.append({
                'type': 'water_stress',
                'severity': 'high',
                'message': f'إجهاد مائي شديد ({self.water_stress_index}%)',
                'recommendation': 'زيادة الري فوراً'
            })
        elif self.water_stress_index > 50:
            alerts.append({
                'type': 'water_stress',
                'severity': 'medium',
                'message': f'إجهاد مائي متوسط ({self.water_stress_index}%)',
                'recommendation': 'مراجعة جدول الري'
            })
        
        if self.nutrient_stress_index > 60:
            alerts.append({
                'type': 'nutrient_deficiency',
                'severity': 'medium',
                'message': f'نقص في العناصر الغذائية ({self.nutrient_stress_index}%)',
                'recommendation': 'إجراء تحليل تربة وتعديل التسميد'
            })
        
        if self.overall_health_score < 30:
            critical_alerts.append({
                'type': 'poor_health',
                'severity': 'critical',
                'message': f'صحة المحصول سيئة جداً ({self.overall_health_score}%)',
                'recommendation': 'تدخل فوري مطلوب'
            })
        
        self.alerts = alerts
        self.critical_alerts = critical_alerts
        self.save(update_fields=['alerts', 'critical_alerts'])


class WeatherData(BaseModel):
    """نموذج بيانات الطقس من الأقمار الصناعية"""
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='weather_data', verbose_name='المزرعة')
    satellite_data = models.ForeignKey(SatelliteData, on_delete=models.CASCADE, related_name='weather_data', verbose_name='بيانات القمر الصناعي')
    
    # البيانات الجوية
    temperature_celsius = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='درجة الحرارة (°C)')
    feels_like_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='درجة الحرارة المحسوسة')
    humidity_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='الرطوبة النسبية (%)')
    pressure_hpa = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='الضغط الجوي (hPa)')
    wind_speed_ms = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='سرعة الرياح (م/ث)')
    wind_direction_degrees = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(360)], verbose_name='اتجاه الرياح (°)')
    
    # الأمطار
    precipitation_mm = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='كمية الأمطار (مم)')
    precipitation_probability = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='احتمالية الأمطار (%)')
    
    # الإشعاع والضوء
    solar_radiation_wm2 = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='الإشعاع الشمسي (وات/م²)')
    uv_index = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, verbose_name='مؤشر الأشعة فوق البنفسجية')
    
    # الغيوم
    cloud_cover_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='نسبة الغيوم (%)')
    visibility_km = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='الرؤية (كم)')
    
    # جودة البيانات
    data_quality = models.CharField(max_length=20, choices=[
        ('excellent', 'ممتاز'),
        ('good', 'جيد'),
        ('fair', 'مقبول'),
        ('poor', 'ضعيف'),
    ], verbose_name='جودة البيانات')
    
    # التوقعات
    forecast_hours = models.PositiveIntegerField(default=0, verbose_name='عدد ساعات التوقع')
    is_forecast = models.BooleanField(default=False, verbose_name='توقع')
    
    class Meta:
        db_table = 'weather_data'
        verbose_name = 'بيانات طقس'
        verbose_name_plural = 'بيانات الطقس'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['farm', 'created_at']),
            models.Index(fields=['is_forecast', 'created_at']),
            models.Index(fields=['temperature_celsius']),
        ]
    
    def __str__(self):
        return f"بيانات طقس {self.farm.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class SatelliteAlert(BaseModel):
    """نموذج تنبيهات الأقمار الصناعية"""
    
    ALERT_TYPES = [
        ('drought_risk', 'خطر جفاف'),
        ('flood_risk', 'خطر فيضان'),
        ('crop_stress', 'إجهاد محصول'),
        ('pest_outbreak', 'ظهور آفة'),
        ('disease_outbreak', 'ظهور مرض'),
        ('growth_anomaly', 'شذوذ في النمو'),
        ('water_logging', 'تراكم مياه'),
        ('fire_risk', 'خطر حريق'),
        ('frost_risk', 'خطر صقيع'),
        ('hail_damage', 'ضرر برد'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('critical', 'حرج'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('acknowledged', 'تم الإقرار'),
        ('resolved', 'مُعالج'),
        ('false_positive', 'إيجابية خاطئة'),
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='satellite_alerts', verbose_name='المزرعة')
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='satellite_alerts', verbose_name='الحقل')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='satellite_alerts', verbose_name='المحصول', null=True, blank=True)
    
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES, verbose_name='نوع التنبيه')
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, verbose_name='شدة التنبيه')
    
    # التفاصيل
    title = models.CharField(max_length=255, verbose_name='عنوان التنبيه')
    description = models.TextField(verbose_name='وصف التنبيه')
    affected_area_hectares = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='المساحة المتأثرة (هكتار)')
    
    # الموقع
    affected_area_polygon = gis_models.PolygonField(geography=True, null=True, blank=True, verbose_name='منطقة التأثر')
    center_point = gis_models.PointField(geography=True, null=True, blank=True, verbose_name='نقطة المركز')
    
    # البيانات الداعمة
    supporting_data = JSONField(default=dict, verbose_name='البيانات الداعمة')
    satellite_images = JSONField(default=list, verbose_name='صور الأقمار الصناعية')
    
    # الحالة
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='الحالة')
    
    # التوصيات
    recommended_actions = JSONField(default=list, verbose_name='الإجراءات الموصى بها')
    urgency_level = models.CharField(max_length=20, choices=[
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('immediate', 'فوري'),
    ], verbose_name='مستوى الإلحاح')
    
    # المتابعة
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_satellite_alerts', verbose_name='أقر بها')
    acknowledged_at = models.DateTimeField(null=True, blank=True, verbose_name='وقت الإقرار')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='وقت المعالجة')
    resolution_notes = models.TextField(blank=True, verbose_name='ملاحظات المعالجة')
    
    # التحقق
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='نسبة الثقة (%)')
    false_positive_probability = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], default=0, verbose_name='احتمالية الإيجابية الخاطئة (%)')
    
    class Meta:
        db_table = 'satellite_alerts'
        verbose_name = 'تنبيه قمر صناعي'
        verbose_name_plural = 'تنبيهات الأقمار الصناعية'
        ordering = ['-severity', '-created_at']
        indexes = [
            models.Index(fields=['farm', 'status']),
            models.Index(fields=['alert_type', 'severity']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"تنبيه {self.get_alert_type_display()} - {self.farm.name}"
    
    def acknowledge(self, user):
        """الإقرار بالتنبيه"""
        self.status = 'acknowledged'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save(update_fields=['status', 'acknowledged_by', 'acknowledged_at'])
    
    def resolve(self, notes=None):
        """حل التنبيه"""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if notes:
            self.resolution_notes = notes
        self.save(update_fields=['status', 'resolved_at', 'resolution_notes'])
    
    def mark_as_false_positive(self):
        """وضع علامة كإيجابية خاطئة"""
        self.status = 'false_positive'
        self.save(update_fields=['status'])


class SatelliteProcessingJob(BaseModel):
    """نموذج مهام معالجة بيانات الأقمار الصناعية"""
    
    JOB_TYPES = [
        ('ndvi_calculation', 'حساب NDVI'),
        ('health_assessment', 'تقييم الصحة'),
        ('change_detection', 'كشف التغيرات'),
        ('classification', 'تصنيف'),
        ('time_series_analysis', 'تحليل السلاسل الزمنية'),
        ('mosaic_creation', 'إنشاء فسيفساء'),
        ('data_download', 'تحميل البيانات'),
    ]
    
    JOB_STATUS = [
        ('queued', 'في الطابور'),
        ('running', 'قيد التشغيل'),
        ('completed', 'مكتمل'),
        ('failed', 'فشل'),
        ('cancelled', 'ملغي'),
    ]
    
    job_type = models.CharField(max_length=30, choices=JOB_TYPES, verbose_name='نوع المهمة')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='satellite_processing_jobs', verbose_name='المزرعة')
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='satellite_processing_jobs', verbose_name='الحقل', null=True, blank=True)
    
    # المعلمات
    parameters = JSONField(default=dict, verbose_name='المعلمات')
    input_data = JSONField(default=dict, verbose_name='البيانات المدخلة')
    
    # الحالة
    status = models.CharField(max_length=20, choices=JOB_STATUS, default='queued', verbose_name='الحالة')
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='نسبة التقدم (%)')
    
    # التوقيت
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='وقت البدء')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='وقت الإكمال')
    estimated_completion_time = models.DateTimeField(null=True, blank=True, verbose_name='وقت الإكمال المتوقع')
    
    # النتائج
    result_data = JSONField(null=True, blank=True, verbose_name='بيانات النتائج')
    output_files = JSONField(default=list, verbose_name='ملفات الناتج')
    result_summary = models.TextField(blank=True, verbose_name='ملخص النتائج')
    
    # الأخطاء
    error_message = models.TextField(blank=True, verbose_name='رسالة الخطأ')
    error_details = JSONField(default=dict, blank=True, verbose_name='تفاصيل الخطأ')
    retry_count = models.PositiveIntegerField(default=0, verbose_name='عدد المحاولات')
    
    # الأداء
    processing_time_seconds = models.PositiveIntegerField(null=True, blank=True, verbose_name='وقت المعالجة (ثواني)')
    memory_usage_mb = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='استخدام الذاكرة (ميجابايت)')
    
    # الأولوية
    priority = models.PositiveIntegerField(default=5, verbose_name='الأولوية')
    
    class Meta:
        db_table = 'satellite_processing_jobs'
        verbose_name = 'مهمة معالجة قمر صناعي'
        verbose_name_plural = 'مهام معالجة الأقمار الصناعية'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['farm', 'status']),
            models.Index(fields=['job_type', 'status']),
            models.Index(fields=['priority', 'status']),
        ]
    
    def __str__(self):
        return f"مهمة {self.get_job_type_display()} - {self.farm.name}"
    
    def start_processing(self):
        """بدء المعالجة"""
        self.status = 'running'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def update_progress(self, percentage):
        """تحديث التقدم"""
        self.progress_percentage = percentage
        self.save(update_fields=['progress_percentage'])
    
    def complete_processing(self, result_data, output_files=None, summary=None):
        """إكمال المعالجة"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.result_data = result_data
        if output_files:
            self.output_files = output_files
        if summary:
            self.result_summary = summary
        
        if self.started_at:
            self.processing_time_seconds = (self.completed_at - self.started_at).total_seconds()
        
        self.save(update_fields=['status', 'completed_at', 'result_data', 'output_files', 'result_summary', 'processing_time_seconds'])
    
    def fail_processing(self, error_message, error_details=None):
        """فشل المعالجة"""
        self.status = 'failed'
        self.error_message = error_message
        if error_details:
            self.error_details = error_details
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'error_details', 'retry_count'])
    
    def cancel_processing(self):
        """إلغاء المعالجة"""
        self.status = 'cancelled'
        self.save(update_fields=['status'])