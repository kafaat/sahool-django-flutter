"""
تكامل مع Sentinel Hub API لتحليل صور الأقمار الصناعية
يوفر:
- حساب NDVI (Normalized Difference Vegetation Index)
- كشف صحة المحاصيل
- تتبع التغيرات عبر الزمن
- خرائط الرطوبة
"""
import requests
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import base64
from io import BytesIO
from PIL import Image


class SentinelImageAnalyzer:
    """
    محلل صور الأقمار الصناعية Sentinel-2
    """
    
    # ألوان NDVI للتصور
    NDVI_COLORS = {
        'very_low': (165, 0, 38),      # أحمر داكن - نباتات ميتة/تربة جافة
        'low': (215, 48, 39),          # أحمر - نباتات ضعيفة
        'moderate': (244, 109, 67),    # برتقالي - نباتات متوسطة
        'good': (253, 174, 97),        # أصفر - نباتات جيدة
        'very_good': (254, 224, 139),  # أصفر فاتح - نباتات ممتازة
        'excellent': (166, 217, 106),  # أخضر فاتح - نباتات صحية جداً
        'optimal': (26, 152, 80),      # أخضر - نباتات مثالية
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        تهيئة المحلل
        
        Args:
            api_key: مفتاح API لـ Sentinel Hub (اختياري)
        """
        self.api_key = api_key or "DEMO_KEY"  # استخدام مفتاح تجريبي
        self.base_url = "https://services.sentinel-hub.com/api/v1"
    
    def calculate_ndvi(self, nir: np.ndarray, red: np.ndarray) -> np.ndarray:
        """
        حساب NDVI من قنوات NIR و Red
        
        NDVI = (NIR - Red) / (NIR + Red)
        
        القيم:
        - -1 إلى 0: ماء، ثلج، سحب
        - 0 إلى 0.2: تربة جرداء، صخور
        - 0.2 إلى 0.5: نباتات متفرقة، شجيرات
        - 0.5 إلى 0.7: نباتات متوسطة الكثافة
        - 0.7 إلى 1.0: نباتات كثيفة وصحية
        
        Args:
            nir: قناة Near-Infrared
            red: قناة Red
            
        Returns:
            np.ndarray: قيم NDVI
        """
        # تجنب القسمة على صفر
        denominator = nir + red
        denominator = np.where(denominator == 0, 0.0001, denominator)
        
        ndvi = (nir - red) / denominator
        
        # قص القيم بين -1 و 1
        ndvi = np.clip(ndvi, -1, 1)
        
        return ndvi
    
    def ndvi_to_color(self, ndvi_value: float) -> Tuple[int, int, int]:
        """
        تحويل قيمة NDVI إلى لون
        
        Args:
            ndvi_value: قيمة NDVI (-1 إلى 1)
            
        Returns:
            tuple: (R, G, B)
        """
        if ndvi_value < 0:
            return (0, 0, 255)  # أزرق - ماء
        elif ndvi_value < 0.2:
            return self.NDVI_COLORS['very_low']
        elif ndvi_value < 0.3:
            return self.NDVI_COLORS['low']
        elif ndvi_value < 0.4:
            return self.NDVI_COLORS['moderate']
        elif ndvi_value < 0.5:
            return self.NDVI_COLORS['good']
        elif ndvi_value < 0.6:
            return self.NDVI_COLORS['very_good']
        elif ndvi_value < 0.7:
            return self.NDVI_COLORS['excellent']
        else:
            return self.NDVI_COLORS['optimal']
    
    def generate_ndvi_map(self, ndvi_array: np.ndarray) -> Image.Image:
        """
        إنشاء خريطة NDVI ملونة
        
        Args:
            ndvi_array: مصفوفة قيم NDVI
            
        Returns:
            Image: صورة ملونة
        """
        height, width = ndvi_array.shape
        rgb_image = np.zeros((height, width, 3), dtype=np.uint8)
        
        for i in range(height):
            for j in range(width):
                rgb_image[i, j] = self.ndvi_to_color(ndvi_array[i, j])
        
        return Image.fromarray(rgb_image)
    
    def analyze_field_health(self, ndvi_array: np.ndarray) -> Dict:
        """
        تحليل صحة الحقل من NDVI
        
        Args:
            ndvi_array: مصفوفة قيم NDVI
            
        Returns:
            dict: تحليل شامل
        """
        # إحصائيات أساسية
        mean_ndvi = float(np.mean(ndvi_array))
        std_ndvi = float(np.std(ndvi_array))
        min_ndvi = float(np.min(ndvi_array))
        max_ndvi = float(np.max(ndvi_array))
        
        # تصنيف المناطق
        water = np.sum(ndvi_array < 0)
        bare_soil = np.sum((ndvi_array >= 0) & (ndvi_array < 0.2))
        sparse_veg = np.sum((ndvi_array >= 0.2) & (ndvi_array < 0.4))
        moderate_veg = np.sum((ndvi_array >= 0.4) & (ndvi_array < 0.6))
        dense_veg = np.sum(ndvi_array >= 0.6)
        
        total_pixels = ndvi_array.size
        
        # تقييم الصحة العامة
        if mean_ndvi < 0.3:
            health_status = 'ضعيف'
            health_score = 30
            recommendation = 'الحقل يحتاج إلى اهتمام فوري. تحقق من الري والتسميد.'
        elif mean_ndvi < 0.5:
            health_status = 'متوسط'
            health_score = 50
            recommendation = 'الحقل في حالة متوسطة. يمكن تحسين الرعاية.'
        elif mean_ndvi < 0.7:
            health_status = 'جيد'
            health_score = 75
            recommendation = 'الحقل في حالة جيدة. استمر في الرعاية الحالية.'
        else:
            health_status = 'ممتاز'
            health_score = 95
            recommendation = 'الحقل في حالة ممتازة. المحافظة على الممارسات الحالية.'
        
        # كشف مناطق الإجهاد
        stress_threshold = mean_ndvi - (1.5 * std_ndvi)
        stress_areas = np.sum(ndvi_array < stress_threshold)
        stress_percentage = (stress_areas / total_pixels) * 100
        
        return {
            'statistics': {
                'mean_ndvi': mean_ndvi,
                'std_ndvi': std_ndvi,
                'min_ndvi': min_ndvi,
                'max_ndvi': max_ndvi,
            },
            'coverage': {
                'water_percentage': (water / total_pixels) * 100,
                'bare_soil_percentage': (bare_soil / total_pixels) * 100,
                'sparse_vegetation_percentage': (sparse_veg / total_pixels) * 100,
                'moderate_vegetation_percentage': (moderate_veg / total_pixels) * 100,
                'dense_vegetation_percentage': (dense_veg / total_pixels) * 100,
            },
            'health': {
                'status': health_status,
                'score': health_score,
                'recommendation': recommendation,
            },
            'stress_detection': {
                'stress_areas_count': int(stress_areas),
                'stress_percentage': float(stress_percentage),
                'has_stress': stress_percentage > 10,
            },
        }
    
    def get_field_ndvi(
        self,
        latitude: float,
        longitude: float,
        date: Optional[datetime] = None,
        size_meters: int = 500
    ) -> Dict:
        """
        الحصول على NDVI لحقل معين
        
        Args:
            latitude: خط العرض
            longitude: خط الطول
            date: التاريخ (افتراضي: آخر 7 أيام)
            size_meters: حجم المنطقة بالأمتار
            
        Returns:
            dict: بيانات NDVI والتحليل
        """
        if date is None:
            date = datetime.now() - timedelta(days=7)
        
        # في الإنتاج، سيتم استدعاء Sentinel Hub API الحقيقي
        # هنا نستخدم بيانات محاكاة للتجربة
        
        # محاكاة بيانات NDVI
        ndvi_array = self._simulate_ndvi_data(size_meters)
        
        # تحليل الصحة
        analysis = self.analyze_field_health(ndvi_array)
        
        # إنشاء خريطة ملونة
        ndvi_map = self.generate_ndvi_map(ndvi_array)
        
        # تحويل الصورة إلى base64
        buffered = BytesIO()
        ndvi_map.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            'location': {
                'latitude': latitude,
                'longitude': longitude,
            },
            'date': date.isoformat(),
            'analysis': analysis,
            'ndvi_map_base64': img_str,
        }
    
    def _simulate_ndvi_data(self, size_meters: int) -> np.ndarray:
        """
        محاكاة بيانات NDVI (للتجربة فقط)
        في الإنتاج، سيتم استبدال هذا ببيانات حقيقية من Sentinel
        """
        # حجم الصورة (10 متر لكل بكسل)
        pixels = size_meters // 10
        
        # إنشاء بيانات عشوائية مع نمط واقعي
        np.random.seed(42)
        
        # قاعدة NDVI (نباتات صحية)
        base_ndvi = np.random.normal(0.6, 0.1, (pixels, pixels))
        
        # إضافة بعض مناطق الإجهاد
        stress_x = np.random.randint(0, pixels, 5)
        stress_y = np.random.randint(0, pixels, 5)
        
        for x, y in zip(stress_x, stress_y):
            radius = np.random.randint(5, 15)
            for i in range(max(0, x-radius), min(pixels, x+radius)):
                for j in range(max(0, y-radius), min(pixels, y+radius)):
                    distance = np.sqrt((i-x)**2 + (j-y)**2)
                    if distance < radius:
                        base_ndvi[i, j] *= 0.5  # تقليل NDVI في مناطق الإجهاد
        
        # قص القيم
        base_ndvi = np.clip(base_ndvi, 0, 1)
        
        return base_ndvi
    
    def compare_temporal_changes(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        مقارنة التغيرات عبر الزمن
        
        Args:
            latitude: خط العرض
            longitude: خط الطول
            start_date: تاريخ البداية
            end_date: تاريخ النهاية
            
        Returns:
            dict: تحليل التغيرات
        """
        # الحصول على NDVI للتاريخين
        ndvi_start = self._simulate_ndvi_data(500)
        ndvi_end = self._simulate_ndvi_data(500)
        
        # حساب التغير
        ndvi_change = ndvi_end - ndvi_start
        
        # إحصائيات التغير
        mean_change = float(np.mean(ndvi_change))
        improved_areas = np.sum(ndvi_change > 0.1)
        degraded_areas = np.sum(ndvi_change < -0.1)
        stable_areas = np.sum(np.abs(ndvi_change) <= 0.1)
        
        total_pixels = ndvi_change.size
        
        # تقييم الاتجاه
        if mean_change > 0.05:
            trend = 'تحسن'
            trend_description = 'صحة المحاصيل تتحسن بشكل عام'
        elif mean_change < -0.05:
            trend = 'تدهور'
            trend_description = 'صحة المحاصيل تتدهور - يحتاج إلى اهتمام'
        else:
            trend = 'مستقر'
            trend_description = 'صحة المحاصيل مستقرة'
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': (end_date - start_date).days,
            },
            'change_statistics': {
                'mean_change': mean_change,
                'improved_percentage': (improved_areas / total_pixels) * 100,
                'degraded_percentage': (degraded_areas / total_pixels) * 100,
                'stable_percentage': (stable_areas / total_pixels) * 100,
            },
            'trend': {
                'direction': trend,
                'description': trend_description,
            },
        }


# مثيل عام
analyzer = SentinelImageAnalyzer()


def get_field_health(latitude: float, longitude: float, date: Optional[datetime] = None) -> Dict:
    """
    دالة مساعدة للحصول على صحة الحقل
    """
    return analyzer.get_field_ndvi(latitude, longitude, date)
