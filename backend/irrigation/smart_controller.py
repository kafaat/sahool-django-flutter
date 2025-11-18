"""
نظام الري الذكي المتقدم
يحسب الاحتياجات المائية بناءً على:
- رطوبة التربة الحالية
- نوع المحصول
- مرحلة النمو
- توقعات الطقس
- نوع التربة
- معدل التبخر
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math


class SmartIrrigationController:
    """
    متحكم الري الذكي
    """
    
    # معاملات المحاصيل (Kc - Crop Coefficient)
    CROP_COEFFICIENTS = {
        'tomato': {
            'initial': 0.6,      # مرحلة النمو الأولية
            'development': 0.7,  # مرحلة التطور
            'mid': 1.15,         # منتصف الموسم
            'late': 0.8,         # نهاية الموسم
        },
        'potato': {
            'initial': 0.5,
            'development': 0.75,
            'mid': 1.15,
            'late': 0.75,
        },
        'corn': {
            'initial': 0.3,
            'development': 0.7,
            'mid': 1.2,
            'late': 0.6,
        },
        'wheat': {
            'initial': 0.3,
            'development': 0.7,
            'mid': 1.15,
            'late': 0.4,
        },
        'rice': {
            'initial': 1.05,
            'development': 1.10,
            'mid': 1.20,
            'late': 0.95,
        },
    }
    
    # خصائص التربة
    SOIL_PROPERTIES = {
        'sandy': {
            'field_capacity': 0.12,        # السعة الحقلية
            'wilting_point': 0.04,         # نقطة الذبول
            'infiltration_rate': 30,       # معدل التسرب (مم/ساعة)
        },
        'loamy': {
            'field_capacity': 0.25,
            'wilting_point': 0.10,
            'infiltration_rate': 15,
        },
        'clay': {
            'field_capacity': 0.35,
            'wilting_point': 0.20,
            'infiltration_rate': 5,
        },
        'silt': {
            'field_capacity': 0.30,
            'wilting_point': 0.12,
            'infiltration_rate': 10,
        },
    }
    
    def __init__(self):
        """تهيئة المتحكم"""
        pass
    
    def calculate_et0(
        self,
        temperature: float,
        humidity: float,
        wind_speed: float,
        solar_radiation: Optional[float] = None
    ) -> float:
        """
        حساب التبخر-نتح المرجعي (ET0) باستخدام معادلة Penman-Monteith المبسطة
        
        Args:
            temperature: درجة الحرارة (°C)
            humidity: الرطوبة النسبية (%)
            wind_speed: سرعة الرياح (m/s)
            solar_radiation: الإشعاع الشمسي (MJ/m²/day) - اختياري
            
        Returns:
            float: ET0 (mm/day)
        """
        # معادلة مبسطة لـ ET0
        # في الإنتاج، يُفضل استخدام معادلة FAO Penman-Monteith الكاملة
        
        # حساب ضغط البخار المشبع
        es = 0.6108 * math.exp((17.27 * temperature) / (temperature + 237.3))
        
        # حساب ضغط البخار الفعلي
        ea = es * (humidity / 100)
        
        # عجز ضغط البخار
        vpd = es - ea
        
        # تقدير الإشعاع إذا لم يكن متوفراً
        if solar_radiation is None:
            # تقدير بسيط بناءً على درجة الحرارة
            solar_radiation = 0.16 * math.sqrt(temperature + 20)
        
        # معادلة مبسطة
        et0 = (0.408 * solar_radiation * (temperature + 5) / 100) + \
              (0.9 * temperature / (temperature + 15)) * wind_speed * vpd
        
        return max(0, et0)
    
    def calculate_crop_water_need(
        self,
        crop_type: str,
        growth_stage: str,
        et0: float,
        area: float
    ) -> float:
        """
        حساب احتياجات المحصول المائية
        
        Args:
            crop_type: نوع المحصول
            growth_stage: مرحلة النمو
            et0: التبخر-نتح المرجعي
            area: مساحة الحقل (هكتار)
            
        Returns:
            float: كمية المياه المطلوبة (m³)
        """
        # الحصول على معامل المحصول
        crop_data = self.CROP_COEFFICIENTS.get(crop_type.lower(), {})
        kc = crop_data.get(growth_stage, 1.0)
        
        # حساب التبخر-نتح للمحصول
        etc = et0 * kc
        
        # تحويل من mm/day إلى m³
        # 1 mm على 1 هكتار = 10 m³
        water_need = etc * area * 10
        
        return water_need
    
    def calculate_optimal_irrigation(
        self,
        field_data: Dict
    ) -> Dict:
        """
        حساب جدول الري الأمثل
        
        Args:
            field_data: بيانات الحقل {
                'crop_type': str,
                'growth_stage': str,
                'soil_type': str,
                'area': float,
                'current_soil_moisture': float,
                'weather': {
                    'temperature': float,
                    'humidity': float,
                    'wind_speed': float,
                    'rainfall_forecast': List[float]  # الأيام القادمة
                }
            }
            
        Returns:
            dict: جدول الري الأمثل
        """
        crop_type = field_data['crop_type']
        growth_stage = field_data['growth_stage']
        soil_type = field_data['soil_type']
        area = field_data['area']
        current_moisture = field_data['current_soil_moisture']
        weather = field_data['weather']
        
        # حساب ET0
        et0 = self.calculate_et0(
            temperature=weather['temperature'],
            humidity=weather['humidity'],
            wind_speed=weather['wind_speed']
        )
        
        # حساب احتياجات المحصول
        daily_water_need = self.calculate_crop_water_need(
            crop_type=crop_type,
            growth_stage=growth_stage,
            et0=et0,
            area=area
        )
        
        # الحصول على خصائص التربة
        soil_props = self.SOIL_PROPERTIES.get(soil_type, self.SOIL_PROPERTIES['loamy'])
        field_capacity = soil_props['field_capacity']
        wilting_point = soil_props['wilting_point']
        
        # حساب المياه المتاحة
        available_water = (field_capacity - wilting_point) * 100  # نسبة مئوية
        
        # حساب العجز المائي
        target_moisture = field_capacity * 0.8  # 80% من السعة الحقلية
        moisture_deficit = max(0, target_moisture - current_moisture)
        
        # كمية المياه المطلوبة لتعويض العجز
        deficit_water = moisture_deficit * area * 10000 * 0.3  # m³
        
        # مراعاة الأمطار المتوقعة
        rainfall_forecast = weather.get('rainfall_forecast', [])
        expected_rainfall = sum(rainfall_forecast[:3]) if rainfall_forecast else 0  # الأيام الثلاثة القادمة
        rainfall_water = expected_rainfall * area * 10  # m³
        
        # الكمية النهائية
        total_water_need = daily_water_need + deficit_water - rainfall_water
        total_water_need = max(0, total_water_need)
        
        # تحديد التوقيت الأمثل
        if expected_rainfall > 10:  # إذا كان هناك أمطار غزيرة متوقعة
            recommendation = 'تأجيل الري - أمطار متوقعة'
            should_irrigate = False
            optimal_time = None
        elif current_moisture < wilting_point * 1.2:
            recommendation = 'ري فوري - رطوبة منخفضة جداً'
            should_irrigate = True
            optimal_time = 'الآن'
        elif current_moisture < target_moisture:
            recommendation = 'ري مجدول - رطوبة أقل من المثالية'
            should_irrigate = True
            # أفضل وقت: الصباح الباكر أو المساء
            current_hour = datetime.now().hour
            if 5 <= current_hour < 8:
                optimal_time = 'الآن (صباحاً)'
            elif 17 <= current_hour < 20:
                optimal_time = 'الآن (مساءً)'
            else:
                optimal_time = 'غداً الساعة 6 صباحاً'
        else:
            recommendation = 'لا حاجة للري - رطوبة كافية'
            should_irrigate = False
            optimal_time = None
        
        # اختيار طريقة الري المثلى
        if soil_type == 'sandy':
            irrigation_method = 'drip'  # تنقيط
            efficiency = 0.90
        elif soil_type == 'clay':
            irrigation_method = 'surface'  # سطحي
            efficiency = 0.60
        else:
            irrigation_method = 'sprinkler'  # رش
            efficiency = 0.75
        
        # تعديل الكمية بناءً على الكفاءة
        adjusted_water = total_water_need / efficiency if should_irrigate else 0
        
        # حساب مدة الري
        flow_rate = 50  # m³/hour (افتراضي)
        duration_hours = adjusted_water / flow_rate if should_irrigate else 0
        
        return {
            'should_irrigate': should_irrigate,
            'recommendation': recommendation,
            'water_requirements': {
                'daily_need': round(daily_water_need, 2),
                'deficit': round(deficit_water, 2),
                'rainfall_contribution': round(rainfall_water, 2),
                'total_need': round(total_water_need, 2),
                'adjusted_for_efficiency': round(adjusted_water, 2),
            },
            'schedule': {
                'optimal_time': optimal_time,
                'duration_hours': round(duration_hours, 2),
                'method': irrigation_method,
                'efficiency': efficiency * 100,
            },
            'soil_status': {
                'current_moisture': current_moisture * 100,
                'target_moisture': target_moisture * 100,
                'field_capacity': field_capacity * 100,
                'wilting_point': wilting_point * 100,
                'status': 'جيد' if current_moisture >= target_moisture else 'يحتاج ري',
            },
            'weather_impact': {
                'et0': round(et0, 2),
                'expected_rainfall_mm': expected_rainfall,
                'temperature': weather['temperature'],
            },
        }
    
    def generate_weekly_schedule(
        self,
        field_data: Dict,
        weather_forecast: List[Dict]
    ) -> List[Dict]:
        """
        إنشاء جدول ري أسبوعي
        
        Args:
            field_data: بيانات الحقل
            weather_forecast: توقعات الطقس لمدة 7 أيام
            
        Returns:
            list: جدول الري اليومي
        """
        schedule = []
        current_moisture = field_data['current_soil_moisture']
        
        for day_idx, daily_weather in enumerate(weather_forecast):
            # تحديث بيانات الحقل لليوم
            field_data_copy = field_data.copy()
            field_data_copy['current_soil_moisture'] = current_moisture
            field_data_copy['weather'] = daily_weather
            
            # حساب الري لليوم
            daily_plan = self.calculate_optimal_irrigation(field_data_copy)
            
            # إضافة التاريخ
            date = datetime.now() + timedelta(days=day_idx)
            daily_plan['date'] = date.strftime('%Y-%m-%d')
            daily_plan['day_name'] = ['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة'][date.weekday()]
            
            schedule.append(daily_plan)
            
            # تحديث الرطوبة للغد (محاكاة)
            if daily_plan['should_irrigate']:
                current_moisture += 0.05  # زيادة بعد الري
            current_moisture -= 0.02  # انخفاض طبيعي
            current_moisture = max(0.1, min(0.4, current_moisture))  # حدود واقعية
        
        return schedule


# مثيل عام
controller = SmartIrrigationController()


def get_irrigation_recommendation(field_data: Dict) -> Dict:
    """
    دالة مساعدة للحصول على توصية الري
    """
    return controller.calculate_optimal_irrigation(field_data)
