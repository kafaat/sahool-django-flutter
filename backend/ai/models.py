"""
نماذج الذكاء الاصطناعي - التكامل الشامل
AI Models - Comprehensive Integration
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
import uuid

from apps.core.models import BaseModel
from apps.farms.models import Farm, Crop, CropVariety
from apps.iot.models import SensorReading

User = get_user_model()


class AIModel(BaseModel):
    """نموذج لإدارة نماذج الذكاء الاصطناعي"""
    
    MODEL_TYPES = [
        ('disease_detection', 'كشف الأمراض'),
        ('yield_prediction', 'تنبؤ الإنتاجية'),
        ('irrigation_optimization', 'تحسين الري'),
        ('pest_prediction', 'تنبؤ الآفات'),
        ('market_price_prediction', 'تنبؤ أسعار السوق'),
        ('weather_prediction', 'تنبؤ الطقس'),
        ('crop_recommendation', 'توصيات المحاصيل'),
        ('soil_analysis', 'تحليل التربة'),
        ('plant_health_assessment', 'تقييم صحة النبات'),
    ]
    
    MODEL_STATUS = [
        ('training', 'قيد التدريب'),
        ('ready', 'جاهز'),
        ('deployed', 'منشور'),
        ('deprecated', 'مهمل'),
        ('error', 'خطأ'),
    ]
    
    name = models.CharField(max_length=255, verbose_name='اسم النموذج')
    model_type = models.CharField(max_length=50, choices=MODEL_TYPES, verbose_name='نوع النموذج')
    version = models.CharField(max_length=50, verbose_name='الإصدار')
    
    # البنية والمعلمات
    architecture = models.CharField(max_length=100, verbose_name='البنية')
    parameters_count = models.PositiveBigIntegerField(verbose_name='عدد المعلمات')
    model_size_mb = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='حجم النموذج (ميجابايت)')
    
    # الأداء
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='الدقة (%)')
    precision = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='الضبط (%)', null=True, blank=True)
    recall = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='الاستدعاء (%)', null=True, blank=True)
    f1_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='F1 Score (%)', null=True, blank=True)
    
    # التدريب
    training_data_size = models.PositiveBigIntegerField(verbose_name='حجم بيانات التدريب')
    training_duration_hours = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='مدة التدريب (ساعات)')
    last_training_date = models.DateTimeField(verbose_name='آخر تاريخ تدريب')
    
    # الحالة والنشر
    status = models.CharField(max_length=20, choices=MODEL_STATUS, default='training', verbose_name='الحالة')
    deployment_date = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ النشر')
    is_active = models.BooleanField(default=False, verbose_name='نشط')
    
    # المعلومات التقنية
    framework = models.CharField(max_length=50, verbose_name='الإطار')
    framework_version = models.CharField(max_length=50, verbose_name='إصدار الإطار')
    
    # الملفات والموارد
    model_file_path = models.CharField(max_length=500, verbose_name='مسار ملف النموذج')
    config_file_path = models.CharField(max_length=500, blank=True, verbose_name='مسار ملف الإعدادات')
    
    # الإعدادات والمعلمات
    hyperparameters = JSONField(default=dict, blank=True, verbose_name='المعلمات الفائقة')
    preprocessing_config = JSONField(default=dict, blank=True, verbose_name='إعدادات المعالجة المسبقة')
    
    # القيود والمتطلبات
    min_input_size = models.JSONField(default=dict, blank=True, verbose_name='الحد الأدنى لحجم المدخلات')
    supported_formats = models.JSONField(default=list, blank=True, verbose_name='الصيغ المدعومة')
    
    # التوثيق
    documentation = models.TextField(blank=True, verbose_name='التوثيق')
    api_endpoint = models.CharField(max_length=200, blank=True, verbose_name='نقطة وصول API')
    
    # الإحصائيات
    total_predictions = models.PositiveBigIntegerField(default=0, verbose_name='إجمالي التنبؤات')
    average_response_time_ms = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name='متوسط وقت الاستجابة (مللي ثانية)')
    
    class Meta:
        db_table = 'ai_models'
        verbose_name = 'نموذج ذكاء اصطناعي'
        verbose_name_plural = 'نماذج الذكاء الاصطناعي'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model_type', 'status']),
            models.Index(fields=['is_active', 'status']),
            models.Index(fields=['version']),
        ]
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.get_model_type_display()})"
    
    def update_performance_metrics(self, accuracy, precision=None, recall=None, f1_score=None):
        """تحديث مقاييس الأداء"""
        self.accuracy = accuracy
        if precision is not None:
            self.precision = precision
        if recall is not None:
            self.recall = recall
        if f1_score is not None:
            self.f1_score = f1_score
        self.save(update_fields=['accuracy', 'precision', 'recall', 'f1_score'])
    
    def increment_predictions(self, response_time_ms):
        """زيادة عدد التنبؤات وتحديث متوسط وقت الاستجابة"""
        self.total_predictions += 1
        if self.average_response_time_ms == 0:
            self.average_response_time_ms = response_time_ms
        else:
            self.average_response_time_ms = (
                (self.average_response_time_ms * (self.total_predictions - 1) + response_time_ms) 
                / self.total_predictions
            )
        self.save(update_fields=['total_predictions', 'average_response_time_ms'])


class DiseaseDetection(BaseModel):
    """نموذج كشف الأمراض النباتية"""
    
    SEVERITY_LEVELS = [
        ('healthy', 'صحي'),
        ('mild', 'خفيف'),
        ('moderate', 'متوسط'),
        ('severe', 'شديد'),
        ('critical', 'حرج'),
    ]
    
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='disease_detections', verbose_name='المحصول')
    image = models.ImageField(upload_to='disease_detection/', verbose_name='صورة المرض')
    
    # نتائج الكشف
    detected_disease = models.CharField(max_length=255, verbose_name='المرض المكتشف')
    disease_code = models.CharField(max_length=50, verbose_name='كود المرض')
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='نسبة الثقة (%)')
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, verbose_name='شدة الإصابة')
    
    # المعلومات التفصيلية
    symptoms = models.TextField(verbose_name='الأعراض')
    affected_area_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='نسبة المنطقة المتأثرة (%)')
    
    # التوصيات
    treatment_recommendations = JSONField(default=dict, verbose_name='توصيات العلاج')
    preventive_measures = JSONField(default=dict, verbose_name='إجراءات الوقاية')
    products_recommended = JSONField(default=list, verbose_name='المنتجات الموصى بها')
    
    # النموذج المستخدم
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='نموذج الذكاء الاصطناعي')
    processing_time_ms = models.PositiveIntegerField(verbose_name='وقت المعالجة (مللي ثانية)')
    
    # المتابعة
    follow_up_required = models.BooleanField(default=True, verbose_name='مطلوب متابعة')
    follow_up_date = models.DateField(null=True, blank=True, verbose_name='تاريخ المتابعة')
    treatment_status = models.CharField(max_length=20, choices=[
        ('not_started', 'لم يبدأ'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('failed', 'فشل'),
    ], default='not_started', verbose_name='حالة العلاج')
    
    # التكلفة
    estimated_treatment_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='تكلفة العلاج المتوقعة')
    
    class Meta:
        db_table = 'disease_detections'
        verbose_name = 'كشف مرض'
        verbose_name_plural = 'كشوفات الأمراض'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['crop', 'detected_disease']),
            models.Index(fields=['severity', 'created_at']),
            models.Index(fields=['treatment_status']),
        ]
    
    def __str__(self):
        return f"كشف {self.detected_disease} - {self.crop.name}"
    
    def save(self, *args, **kwargs):
        if self.follow_up_required and not self.follow_up_date:
            self.follow_up_date = timezone.now().date() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
    
    def update_treatment_status(self, status):
        """تحديث حالة العلاج"""
        self.treatment_status = status
        self.save(update_fields=['treatment_status'])


class YieldPrediction(BaseModel):
    """نموذج تنبؤات الإنتاجية"""
    
    PREDICTION_TYPES = [
        ('crop_yield', 'إنتاجية محصول'),
        ('farm_yield', 'إنتاجية مزرعة'),
        ('field_yield', 'إنتاجية حقل'),
        ('variety_yield', 'إنتاجية صنف'),
    ]
    
    prediction_type = models.CharField(max_length=20, choices=PREDICTION_TYPES, verbose_name='نوع التنبؤ')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='yield_predictions', verbose_name='المحصول')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='yield_predictions', verbose_name='المزرعة')
    
    # بيانات المدخلات
    input_data = JSONField(verbose_name='بيانات المدخلات')
    environmental_factors = JSONField(default=dict, verbose_name='العوامل البيئية')
    historical_data = JSONField(default=dict, verbose_name='البيانات التاريخية')
    
    # نتائج التنبؤ
    predicted_yield = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='الإنتاجية المتوقعة')
    confidence_interval_lower = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='حد الثقة الأدنى')
    confidence_interval_upper = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='حد الثقة الأعلى')
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='مستوى الثقة (%)')
    
    # التواريخ
    prediction_date = models.DateField(verbose_name='تاريخ التنبؤ')
    predicted_harvest_date = models.DateField(verbose_name='تاريخ الحصاد المتوقع')
    
    # العوامل المؤثرة
    key_factors = JSONField(default=dict, verbose_name='العوامل الرئيسية المؤثرة')
    risk_factors = JSONField(default=dict, verbose_name='عوامل الخطورة')
    
    # التوصيات
    recommendations = JSONField(default=dict, verbose_name='التوصيات')
    optimization_suggestions = JSONField(default=dict, verbose_name='اقتراحات التحسين')
    
    # النموذج المستخدم
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='نموذج الذكاء الاصطناعي')
    
    # الدقة والتحقق
    actual_yield = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='الإنتاجية الفعلية')
    accuracy_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='نسبة الدقة (%)')
    
    # التكلفة والإيرادات
    estimated_revenue = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='الإيرادات المتوقعة')
    production_cost = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='تكلفة الإنتاج')
    expected_profit = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='الربح المتوقع')
    
    class Meta:
        db_table = 'yield_predictions'
        verbose_name = 'تنبؤ إنتاجية'
        verbose_name_plural = 'تنبؤات الإنتاجية'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['crop', 'prediction_date']),
            models.Index(fields=['farm', 'predicted_harvest_date']),
            models.Index(fields=['prediction_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"تنبؤ إنتاجية {self.crop.name} - {self.predicted_yield}"
    
    def update_actual_yield(self, actual_yield):
        """تحديث الإنتاجية الفعلية وحساب الدقة"""
        self.actual_yield = actual_yield
        if self.predicted_yield > 0:
            self.accuracy_percentage = 100 - abs((actual_yield - self.predicted_yield) / self.predicted_yield * 100)
        self.save(update_fields=['actual_yield', 'accuracy_percentage'])


class IrrigationRecommendation(BaseModel):
    """نموذج توصيات الري الذكي"""
    
    RECOMMENDATION_TYPES = [
        ('irrigation_schedule', 'جدول الري'),
        ('water_amount', 'كمية المياه'),
        ('irrigation_method', 'طريقة الري'),
        ('timing', 'التوقيت'),
        ('frequency', 'التكرار'),
        ('emergency', 'طارئ'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('urgent', 'عاجل'),
    ]
    
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='irrigation_recommendations', verbose_name='المحصول')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='irrigation_recommendations', verbose_name='المزرعة')
    
    recommendation_type = models.CharField(max_length=30, choices=RECOMMENDATION_TYPES, verbose_name='نوع التوصية')
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, verbose_name='الأولوية')
    
    # التوصية
    title = models.CharField(max_length=255, verbose_name='عنوان التوصية')
    description = models.TextField(verbose_name='وصف التوصية')
    
    # البيانات التقنية
    recommended_water_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='كمية المياه الموصى بها (لتر)')
    recommended_frequency = models.CharField(max_length=50, blank=True, verbose_name='التكرار الموصى به')
    recommended_timing = models.JSONField(default=dict, blank=True, verbose_name='الوقت الموصى به')
    
    # العوامل المؤثرة
    trigger_factors = JSONField(default=dict, verbose_name='العوامل المؤثرة')
    environmental_conditions = JSONField(default=dict, verbose_name='الظروف البيئية')
    soil_conditions = JSONField(default=dict, verbose_name='ظروف التربة')
    crop_conditions = JSONField(default=dict, verbose_name='حالة المحصول')
    
    # التوقعات
    expected_water_savings = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='الوفورات المتوقعة في المياه (%)')
    expected_yield_improvement = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='التحسن المتوقع في الإنتاجية (%)')
    
    # التنفيذ
    is_implemented = models.BooleanField(default=False, verbose_name='تم التنفيذ')
    implementation_date = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ التنفيذ')
    implemented_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='نفذ بواسطة')
    
    # النتائج
    implementation_result = JSONField(default=dict, blank=True, verbose_name='نتائج التنفيذ')
    effectiveness_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='درجة الفعالية')
    
    # النموذج المستخدم
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='نموذج الذكاء الاصطناعي')
    
    # المدة الصلاحية
    valid_until = models.DateTimeField(verbose_name='صالح حتى')
    is_expired = models.BooleanField(default=False, verbose_name='منتهي الصلاحية')
    
    class Meta:
        db_table = 'irrigation_recommendations'
        verbose_name = 'توصية ري'
        verbose_name_plural = 'توصيات الري'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['crop', 'priority']),
            models.Index(fields=['farm', 'is_implemented']),
            models.Index(fields=['valid_until', 'is_expired']),
        ]
    
    def __str__(self):
        return f"توصية {self.title} - {self.crop.name}"
    
    def save(self, *args, **kwargs):
        if not self.valid_until:
            self.valid_until = timezone.now() + timezone.timedelta(days=7)
        
        if self.valid_until < timezone.now():
            self.is_expired = True
        
        if self.is_implemented and not self.implementation_date:
            self.implementation_date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def mark_as_implemented(self, user, result_data=None):
        """وضع علامة على التوصية كمنفذة"""
        self.is_implemented = True
        self.implemented_by = user
        if result_data:
            self.implementation_result = result_data
        self.save(update_fields=['is_implemented', 'implemented_by', 'implementation_date', 'implementation_result'])


class PestPrediction(BaseModel):
    """نموذج تنبؤات الآفات"""
    
    PEST_TYPES = [
        ('insects', 'حشرات'),
        ('fungi', 'فطريات'),
        ('bacteria', 'بكتيريا'),
        ('viruses', 'فيروسات'),
        ('nematodes', 'نيماتودا'),
        ('weeds', 'أعشاب ضارة'),
        ('rodents', 'قوارض'),
        ('birds', 'طيور'),
    ]
    
    RISK_LEVELS = [
        ('very_low', 'منخفض جداً'),
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('very_high', 'عالي جداً'),
    ]
    
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='pest_predictions', verbose_name='المحصول')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='pest_predictions', verbose_name='المزرعة')
    
    pest_type = models.CharField(max_length=20, choices=PEST_TYPES, verbose_name='نوع الآفة')
    predicted_pest = models.CharField(max_length=255, verbose_name='الآفة المتوقعة')
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS, verbose_name='مستوى الخطورة')
    
    # احتمالية الظهور
    probability = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='احتمالية الظهور (%)')
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='نسبة الثقة (%)')
    
    # التوقيت
    predicted_occurrence_date = models.DateField(verbose_name='تاريخ الظهور المتوقع')
    prediction_horizon_days = models.PositiveIntegerField(verbose_name='أفق التنبؤ (أيام)')
    
    # العوامل المؤثرة
    environmental_triggers = JSONField(default=dict, verbose_name='المحفزات البيئية')
    crop_stage_risk = JSONField(default=dict, verbose_name='مخاطر مرحلة النمو')
    historical_occurrences = JSONField(default=dict, verbose_name='الحالات السابقة')
    
    # التوصيات
    prevention_methods = JSONField(default=dict, verbose_name='طرق الوقاية')
    treatment_options = JSONField(default=dict, verbose_name='خيارات العلاج')
    monitoring_schedule = JSONField(default=dict, verbose_name='جدول المراقبة')
    
    # النموذج المستخدم
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='نموذج الذكاء الاصطناعي')
    
    # التحقق والمتابعة
    actual_occurrence = models.BooleanField(default=False, verbose_name='وقعت فعلاً')
    actual_occurrence_date = models.DateField(null=True, blank=True, verbose_name='تاريخ الظهور الفعلي')
    severity_if_occurred = models.CharField(max_length=20, choices=RISK_LEVELS, blank=True, verbose_name='الشدة إذا وقعت')
    
    # التكلفة والأثر
    estimated_damage_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='التكلفة المتوقعة للضرر')
    prevention_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='تكلفة الوقاية')
    
    class Meta:
        db_table = 'pest_predictions'
        verbose_name = 'تنبؤ آفة'
        verbose_name_plural = 'تنبؤات الآفات'
        ordering = ['-probability', '-created_at']
        indexes = [
            models.Index(fields=['crop', 'risk_level']),
            models.Index(fields=['farm', 'predicted_occurrence_date']),
            models.Index(fields=['pest_type', 'probability']),
        ]
    
    def __str__(self):
        return f"تنبؤ {self.predicted_pest} - {self.crop.name} ({self.probability}%)"
    
    def update_actual_occurrence(self, occurred, occurrence_date=None, severity=None):
        """تحديث الظهور الفعلي"""
        self.actual_occurrence = occurred
        if occurred:
            self.actual_occurrence_date = occurrence_date or timezone.now().date()
            if severity:
                self.severity_if_occurred = severity
        self.save(update_fields=['actual_occurrence', 'actual_occurrence_date', 'severity_if_occurred'])


class MarketPricePrediction(BaseModel):
    """نموذج تنبؤات أسعار السوق"""
    
    crop_category = models.CharField(max_length=50, verbose_name='فئة المحصول')
    crop_name = models.CharField(max_length=100, verbose_name='اسم المحصول')
    region = models.CharField(max_length=100, verbose_name='المنطقة')
    
    # التنبؤات
    predicted_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='السعر المتوقع')
    price_unit = models.CharField(max_length=20, default='per_kg', verbose_name='وحدة السعر')
    currency = models.CharField(max_length=10, default='YER', verbose_name='العملة')
    
    # نطاق السعر
    price_range_lower = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='الحد الأدنى للسعر')
    price_range_upper = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='الحد الأعلى للسعر')
    confidence_interval = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='نطاق الثقة')
    
    # التوقيت
    prediction_date = models.DateField(verbose_name='تاريخ التنبؤ')
    target_date = models.DateField(verbose_name='التاريخ المستهدف')
    prediction_horizon_days = models.PositiveIntegerField(verbose_name='أفق التنبؤ (أيام)')
    
    # العوامل المؤثرة
    market_factors = JSONField(default=dict, verbose_name='عوامل السوق')
    seasonal_factors = JSONField(default=dict, verbose_name='العوامل الموسمية')
    economic_indicators = JSONField(default=dict, verbose_name='المؤشرات الاقتصادية')
    weather_impact = JSONField(default=dict, verbose_name='تأثير الطقس')
    
    # التوصيات
    selling_recommendation = models.CharField(max_length=20, choices=[
        ('sell_now', 'بيع الآن'),
        ('wait', 'الانتظار'),
        ('sell_later', 'بيع لاحقاً'),
        ('hold', 'الاحتفاظ'),
    ], verbose_name='توصية البيع')
    recommendation_reason = models.TextField(verbose_name='سبب التوصية')
    optimal_selling_window = JSONField(default=dict, verbose_name='الفترة المثلى للبيع')
    
    # النموذج المستخدم
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='نموذج الذكاء الاصطناعي')
    
    # التحقق
    actual_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='السعر الفعلي')
    prediction_accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='دقة التنبؤ (%)')
    
    # المخاطر
    risk_assessment = JSONField(default=dict, verbose_name='تقييم المخاطر')
    volatility_index = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='مؤشر التقلبات')
    
    class Meta:
        db_table = 'market_price_predictions'
        verbose_name = 'تنبؤ سعر السوق'
        verbose_name_plural = 'تنبؤات أسعار السوق'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['crop_category', 'target_date']),
            models.Index(fields=['region', 'prediction_date']),
            models.Index(fields=['selling_recommendation']),
        ]
    
    def __str__(self):
        return f"تنبؤ سعر {self.crop_name} - {self.predicted_price} {self.currency}"
    
    def update_actual_price(self, actual_price):
        """تحديث السعر الفعلي وحساب الدقة"""
        self.actual_price = actual_price
        if self.predicted_price > 0:
            self.prediction_accuracy = 100 - abs((actual_price - self.predicted_price) / self.predicted_price * 100)
        self.save(update_fields=['actual_price', 'prediction_accuracy'])


class SoilAnalysis(BaseModel):
    """نموذج تحليل التربة بالذكاء الاصطناعي"""
    
    ANALYSIS_TYPES = [
        ('nutrient_analysis', 'تحليل العناصر الغذائية'),
        ('contamination_detection', 'كشف التلوث'),
        ('texture_analysis', 'تحليل النسيج'),
        ('moisture_analysis', 'تحليل الرطوبة'),
        ('ph_analysis', 'تحليل الحموضة'),
        ('organic_matter_analysis', 'تحليل المادة العضوية'),
    ]
    
    field = models.ForeignKey('fields.Field', on_delete=models.CASCADE, related_name='soil_analyses', verbose_name='الحقل')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='soil_analyses', verbose_name='المزرعة')
    
    analysis_type = models.CharField(max_length=30, choices=ANALYSIS_TYPES, verbose_name='نوع التحليل')
    
    # بيانات التربة
    soil_data = JSONField(verbose_name='بيانات التربة')
    sensor_readings = models.ManyToManyField(SensorReading, blank=True, verbose_name='قراءات المستشعرات')
    
    # نتائج التحليل
    analysis_results = JSONField(verbose_name='نتائج التحليل')
    nutrient_levels = JSONField(default=dict, verbose_name='مستويات العناصر الغذائية')
    deficiencies = JSONField(default=list, verbose_name='العناصر الناقصة')
    excesses = JSONField(default=list, verbose_name='العناصر الزائدة')
    
    # التوصيات
    fertilizer_recommendations = JSONField(default=dict, verbose_name='توصيات الأسمدة')
    soil_amendments = JSONField(default=dict, verbose_name='تحسينات التربة')
    irrigation_adjustments = JSONField(default=dict, verbose_name='تعديلات الري')
    
    # الجودة والصلاحية
    soil_quality_score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='درجة جودة التربة')
    suitability_for_crops = JSONField(default=dict, verbose_name='الملاءمة للمحاصيل')
    
    # النموذج المستخدم
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='نموذج الذكاء الاصطناعي')
    
    # الموقع الجغرافي
    gps_coordinates = models.JSONField(default=dict, verbose_name='إحداثيات GPS')
    depth_cm = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='العمق (سم)')
    
    # التاريخ والوقت
    sampling_date = models.DateField(verbose_name='تاريخ أخذ العينة')
    analysis_date = models.DateTimeField(default=timezone.now, verbose_name='تاريخ التحليل')
    
    # التحقق
    lab_verification = JSONField(default=dict, blank=True, verbose_name='التحقق المختبري')
    accuracy_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='درجة الدقة')
    
    class Meta:
        db_table = 'soil_analyses'
        verbose_name = 'تحليل تربة'
        verbose_name_plural = 'تحليلات التربة'
        ordering = ['-analysis_date']
        indexes = [
            models.Index(fields=['field', 'analysis_type']),
            models.Index(fields=['farm', 'sampling_date']),
            models.Index(fields=['soil_quality_score']),
        ]
    
    def __str__(self):
        return f"تحليل {self.get_analysis_type_display()} - {self.field.name}"
    
    def update_accuracy(self, lab_results):
        """تحديث الدقة بناءً على نتائج المختبر"""
        self.lab_verification = lab_results
        # حساب الدقة بناءً على المقارنة
        # هذا سيكون معقداً حسب نوع التحليل
        self.accuracy_score = 95.0  # مثال
        self.save(update_fields=['lab_verification', 'accuracy_score'])


class AIProcessingLog(BaseModel):
    """سجل معالجات الذكاء الاصطناعي"""
    
    PROCESSING_TYPES = [
        ('disease_detection', 'كشف الأمراض'),
        ('yield_prediction', 'تنبؤ الإنتاجية'),
        ('irrigation_recommendation', 'توصيات الري'),
        ('pest_prediction', 'تنبؤ الآفات'),
        ('price_prediction', 'تنبؤ الأسعار'),
        ('soil_analysis', 'تحليل التربة'),
        ('image_analysis', 'تحليل الصور'),
        ('sensor_data_analysis', 'تحليل بيانات المستشعرات'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'معلق'),
        ('processing', 'قيد المعالجة'),
        ('completed', 'مكتمل'),
        ('failed', 'فشل'),
        ('timeout', 'انتهاء الوقت'),
    ]
    
    processing_type = models.CharField(max_length=30, choices=PROCESSING_TYPES, verbose_name='نوع المعالجة')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_processing_logs', verbose_name='المستخدم')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='ai_processing_logs', verbose_name='المزرعة')
    
    # المدخلات
    input_data = JSONField(verbose_name='بيانات المدخلات')
    input_size_mb = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='حجم المدخلات (ميجابايت)')
    
    # النتائج
    output_data = JSONField(null=True, blank=True, verbose_name='بيانات الناتج')
    result_summary = models.TextField(blank=True, verbose_name='ملخص النتائج')
    
    # الأداء
    processing_time_ms = models.PositiveIntegerField(verbose_name='وقت المعالجة (مللي ثانية)')
    memory_usage_mb = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='استخدام الذاكرة (ميجابايت)')
    
    # الحالة
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    error_message = models.TextField(blank=True, verbose_name='رسالة الخطأ')
    error_code = models.CharField(max_length=50, blank=True, verbose_name='كود الخطأ')
    
    # النموذج المستخدم
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='نموذج الذكاء الاصطناعي')
    model_version = models.CharField(max_length=50, blank=True, verbose_name='إصدار النموذج')
    
    # التكلفة
    processing_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='تكلفة المعالجة')
    
    # الأجهزة
    gpu_used = models.BooleanField(default=False, verbose_name='استخدم GPU')
    gpu_model = models.CharField(max_length=100, blank=True, verbose_name='موديل GPU')
    
    class Meta:
        db_table = 'ai_processing_logs'
        verbose_name = 'سجل معالجة AI'
        verbose_name_plural = 'سجلات معالجات AI'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'processing_type']),
            models.Index(fields=['farm', 'status']),
            models.Index(fields=['processing_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"معالجة {self.get_processing_type_display()} - {self.user.username}"
    
    def mark_as_completed(self, output_data, processing_time_ms, memory_usage_mb):
        """وضع علامة كمكتمل"""
        self.status = 'completed'
        self.output_data = output_data
        self.processing_time_ms = processing_time_ms
        self.memory_usage_mb = memory_usage_mb
        self.save(update_fields=['status', 'output_data', 'processing_time_ms', 'memory_usage_mb'])
    
    def mark_as_failed(self, error_message, error_code=None):
        """وضع علامة كفاشل"""
        self.status = 'failed'
        self.error_message = error_message
        if error_code:
            self.error_code = error_code
        self.save(update_fields=['status', 'error_message', 'error_code'])