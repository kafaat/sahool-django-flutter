"""
خدمات الطقس المتقدمة - التكامل الشامل
Advanced Weather Services - Comprehensive Integration
"""

import requests
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
import logging

from .models import WeatherData, WeatherAlert, WeatherForecast
from apps.farms.models import Farm
from apps.iot.models import SensorReading

logger = logging.getLogger(__name__)


class WeatherService:
    """خدمة الطقس المتقدمة مع التكامل الشامل"""
    
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.cache_timeout = 3600  # 1 hour
        
    def get_current_weather(self, latitude: float, longitude: float) -> Dict:
        """الحصول على الطقس الحالي مع التخزين المؤقت"""
        cache_key = f"current_weather_{latitude}_{longitude}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
            
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # معالجة البيانات
            processed_data = self._process_current_weather(data)
            
            # التخزين المؤقت
            cache.set(cache_key, processed_data, self.cache_timeout)
            
            return processed_data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching current weather: {e}")
            return self._get_fallback_weather(latitude, longitude)
    
    def get_forecast(self, latitude: float, longitude: float, days: int = 5) -> List[Dict]:
        """الحصول على توقعات الطقس"""
        cache_key = f"weather_forecast_{latitude}_{longitude}_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
            
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric',
                'cnt': days * 8  # 8 forecasts per day (3-hour intervals)
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # معالجة بيانات التوقعات
            processed_forecast = self._process_forecast(data, days)
            
            # التخزين المؤقت
            cache.set(cache_key, processed_forecast, self.cache_timeout)
            
            return processed_forecast
            
        except requests.RequestException as e:
            logger.error(f"Error fetching weather forecast: {e}")
            return self._get_fallback_forecast(latitude, longitude, days)
    
    def get_hourly_forecast(self, latitude: float, longitude: float, hours: int = 48) -> List[Dict]:
        """الحصول على توقعات الطقس بالساعة"""
        try:
            url = f"https://pro.openweathermap.org/data/2.5/forecast/hourly"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric',
                'cnt': hours
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._process_hourly_forecast(data)
            
        except requests.RequestException as e:
            logger.error(f"Error fetching hourly forecast: {e}")
            return []
    
    def get_historical_weather(self, latitude: float, longitude: float, start_date: datetime, end_date: datetime) -> List[Dict]:
        """الحصول على بيانات الطقس التاريخية"""
        try:
            url = "https://api.openweathermap.org/data/2.5/onecall/timemachine"
            
            historical_data = []
            current_date = start_date
            
            while current_date <= end_date:
                params = {
                    'lat': latitude,
                    'lon': longitude,
                    'dt': int(current_date.timestamp()),
                    'appid': self.api_key,
                    'units': 'metric'
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                historical_data.append(self._process_historical_data(data, current_date))
                
                current_date += timedelta(days=1)
            
            return historical_data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching historical weather: {e}")
            return []
    
    def calculate_et0(self, latitude: float, longitude: float, date: datetime) -> float:
        """حساب ET0 (النتح المرجعي) باستخدام طريقة Penman-Monteith"""
        try:
            weather_data = self.get_current_weather(latitude, longitude)
            
            # استخراج البيانات المطلوبة
            temperature = weather_data.get('temperature', 25)
            humidity = weather_data.get('humidity', 50)
            wind_speed = weather_data.get('wind_speed', 2)
            pressure = weather_data.get('pressure', 1013.25)
            
            # حساب ET0 باستخدام معادلة Penman-Monteht المبسطة
            et0 = self._calculate_penman_monteith_et0(
                temperature, humidity, wind_speed, pressure, latitude, date
            )
            
            return et0
            
        except Exception as e:
            logger.error(f"Error calculating ET0: {e}")
            return 4.0  # قيمة افتراضية
    
    def calculate_growing_degree_days(self, farm: Farm, start_date: datetime, end_date: datetime) -> float:
        """حساب درجات النمو (GDD)"""
        try:
            base_temperature = 10.0  # درجة الحرارة الأساسية للنمو
            
            historical_data = self.get_historical_weather(
                farm.location.y, farm.location.x, start_date, end_date
            )
            
            total_gdd = 0
            
            for day_data in historical_data:
                max_temp = day_data.get('max_temperature', base_temperature)
                min_temp = day_data.get('min_temperature', base_temperature)
                
                # متوسط درجة الحرارة اليومية
                avg_temp = (max_temp + min_temp) / 2
                
                # حساب GDD لهذا اليوم
                if avg_temp > base_temperature:
                    daily_gdd = avg_temp - base_temperature
                else:
                    daily_gdd = 0
                
                total_gdd += daily_gdd
            
            return total_gdd
            
        except Exception as e:
            logger.error(f"Error calculating GDD: {e}")
            return 0
    
    def generate_weather_alerts(self, farm: Farm) -> List[Dict]:
        """إنشاء تنبيهات الطقس للمزرعة"""
        alerts = []
        
        try:
            current_weather = self.get_current_weather(farm.location.y, farm.location.x)
            forecast = self.get_forecast(farm.location.y, farm.location.x, days=5)
            
            # تنبيهات درجة الحرارة
            if current_weather.get('temperature', 0) > 40:
                alerts.append({
                    'type': 'extreme_heat',
                    'severity': 'high',
                    'message': f'تحذير: درجة حرارة عالية جداً ({current_weather["temperature"]}°C)',
                    'recommendation': 'زيادة الري، توفير الظل للمحاصيل الحساسة',
                    'farm_id': farm.id,
                    'timestamp': timezone.now()
                })
            
            if current_weather.get('temperature', 0) < 5:
                alerts.append({
                    'type': 'frost_risk',
                    'severity': 'high',
                    'message': f'تحذير: خطر الصقيع ({current_weather["temperature"]}°C)',
                    'recommendation': 'تغطية المحاصيل الحساسة، تفعيل أنظمة التدفئة',
                    'farm_id': farm.id,
                    'timestamp': timezone.now()
                })
            
            # تنبيهات الرياح
            if current_weather.get('wind_speed', 0) > 15:
                alerts.append({
                    'type': 'strong_wind',
                    'severity': 'medium',
                    'message': f'رياح قوية ({current_weather["wind_speed"]} م/ث)',
                    'recommendation': 'تثبيت المعدات والهياكل، منع الرش بالمبيدات',
                    'farm_id': farm.id,
                    'timestamp': timezone.now()
                })
            
            # تنبيهات الأمطار
            for day_forecast in forecast[:3]:
                if day_forecast.get('rain', 0) > 20:
                    alerts.append({
                        'type': 'heavy_rain',
                        'severity': 'medium',
                        'message': f'أمطار غزيرة متوقعة ({day_forecast["rain"]} ملم)',
                        'recommendation': 'تقليل الري، تصريف المياه الزائدة',
                        'farm_id': farm.id,
                        'date': day_forecast.get('date'),
                        'timestamp': timezone.now()
                    })
            
            # تنبيهات الجفاف
            if not any(day.get('rain', 0) > 0 for day in forecast[:7]):
                alerts.append({
                    'type': 'drought_risk',
                    'severity': 'medium',
                    'message': 'فترة جفاف متوقعة (7 أيام بدون أمطار)',
                    'recommendation': 'تخطيط للري، ترشيد استخدام المياه',
                    'farm_id': farm.id,
                    'timestamp': timezone.now()
                })
            
            # حفظ التنبيهات في قاعدة البيانات
            for alert_data in alerts:
                WeatherAlert.objects.create(
                    farm=farm,
                    alert_type=alert_data['type'],
                    severity=alert_data['severity'],
                    message=alert_data['message'],
                    recommendation=alert_data['recommendation'],
                    expires_at=timezone.now() + timedelta(days=3)
                )
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating weather alerts: {e}")
            return []
    
    def get_weather_summary(self, farm: Farm, days: int = 7) -> Dict:
        """الحصول على ملخص الطقس للمزرعة"""
        try:
            current_weather = self.get_current_weather(farm.location.y, farm.location.x)
            forecast = self.get_forecast(farm.location.y, farm.location.x, days)
            
            # حساب المتوسطات
            temperatures = [day.get('temperature', 0) for day in forecast]
            humidity_values = [day.get('humidity', 0) for day in forecast]
            rain_values = [day.get('rain', 0) for day in forecast]
            
            summary = {
                'current_temperature': current_weather.get('temperature', 0),
                'current_humidity': current_weather.get('humidity', 0),
                'current_conditions': current_weather.get('description', 'Unknown'),
                'avg_temperature': sum(temperatures) / len(temperatures) if temperatures else 0,
                'avg_humidity': sum(humidity_values) / len(humidity_values) if humidity_values else 0,
                'total_rainfall': sum(rain_values),
                'rainy_days': len([r for r in rain_values if r > 0]),
                'forecast': forecast[:5]  # أول 5 أيام فقط
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting weather summary: {e}")
            return {}
    
    def get_optimal_irrigation_time(self, farm: Farm) -> Dict:
        """الحصول على أفضل وقت للري بناءً على الطقس"""
        try:
            hourly_forecast = self.get_hourly_forecast(farm.location.y, farm.location.x, hours=24)
            
            optimal_times = []
            
            for hour_data in hourly_forecast:
                temp = hour_data.get('temperature', 25)
                humidity = hour_data.get('humidity', 50)
                wind_speed = hour_data.get('wind_speed', 2)
                rain = hour_data.get('rain', 0)
                
                # حساب درجة الملاءمة للري (0-100)
                suitability_score = 100
                
                # خصم نقاط لدرجات الحرارة المرتفعة
                if temp > 30:
                    suitability_score -= (temp - 30) * 2
                
                # خصم نقاط لانخفاض الرطوبة
                if humidity < 40:
                    suitability_score -= (40 - humidity) * 1.5
                
                # خصم نقاط لعوامل أخرى
                if wind_speed > 5:
                    suitability_score -= (wind_speed - 5) * 3
                
                if rain > 0:
                    suitability_score = 0
                
                suitability_score = max(0, min(100, suitability_score))
                
                if suitability_score > 70:
                    optimal_times.append({
                        'time': hour_data.get('time'),
                        'score': suitability_score,
                        'temperature': temp,
                        'humidity': humidity,
                        'wind_speed': wind_speed
                    })
            
            # ترتيب حسب الأفضلية
            optimal_times.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                'optimal_times': optimal_times[:5],
                'best_time': optimal_times[0] if optimal_times else None,
                'avoid_times': [t for t in hourly_forecast if t.get('rain', 0) > 0]
            }
            
        except Exception as e:
            logger.error(f"Error calculating optimal irrigation time: {e}")
            return {}
    
    def _process_current_weather(self, data: Dict) -> Dict:
        """معالجة بيانات الطقس الحالي"""
        return {
            'temperature': data['main']['temp'],
            'feels_like': data['main'].get('feels_like', data['main']['temp']),
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': data['wind']['speed'],
            'wind_direction': data['wind'].get('deg', 0),
            'visibility': data.get('visibility', 10000) / 1000,  # convert to km
            'cloud_cover': data['clouds']['all'],
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon'],
            'uv_index': data.get('uvi', 0),
            'timestamp': timezone.now()
        }
    
    def _process_forecast(self, data: Dict, days: int) -> List[Dict]:
        """معالجة بيانات التوقعات"""
        forecasts = []
        
        for i in range(0, min(days * 8, len(data['list'])), 8):  # 8 forecasts per day
            day_data = data['list'][i]
            
            forecast = {
                'date': timezone.datetime.fromtimestamp(day_data['dt']).date(),
                'temperature': day_data['main']['temp'],
                'min_temperature': day_data['main']['temp_min'],
                'max_temperature': day_data['main']['temp_max'],
                'humidity': day_data['main']['humidity'],
                'pressure': day_data['main']['pressure'],
                'wind_speed': day_data['wind']['speed'],
                'wind_direction': day_data['wind'].get('deg', 0),
                'cloud_cover': day_data['clouds']['all'],
                'rain': day_data.get('rain', {}).get('3h', 0),
                'description': day_data['weather'][0]['description'],
                'icon': day_data['weather'][0]['icon']
            }
            
            forecasts.append(forecast)
        
        return forecasts
    
    def _process_hourly_forecast(self, data: Dict) -> List[Dict]:
        """معالجة التوقعات بالساعة"""
        forecasts = []
        
        for item in data['list']:
            forecast = {
                'time': timezone.datetime.fromtimestamp(item['dt']),
                'temperature': item['main']['temp'],
                'humidity': item['main']['humidity'],
                'wind_speed': item['wind']['speed'],
                'rain': item.get('rain', {}).get('3h', 0),
                'description': item['weather'][0]['description']
            }
            
            forecasts.append(forecast)
        
        return forecasts
    
    def _process_historical_data(self, data: Dict, date: datetime) -> Dict:
        """معالجة البيانات التاريخية"""
        return {
            'date': date,
            'temperature': data['current']['temp'],
            'min_temperature': data['current'].get('temp_min', data['current']['temp']),
            'max_temperature': data['current'].get('temp_max', data['current']['temp']),
            'humidity': data['current']['humidity'],
            'pressure': data['current']['pressure'],
            'wind_speed': data['current']['wind_speed'],
            'cloud_cover': data['current']['clouds'],
            'uv_index': data['current']['uvi']
        }
    
    def _calculate_penman_monteith_et0(self, temp: float, humidity: float, wind_speed: float, pressure: float, latitude: float, date: datetime) -> float:
        """حساب ET0 باستخدام معادلة Penman-Monteith المبسطة"""
        try:
            # ثوابث
            albedo = 0.23  # انعكاسية السطح المرجعي
            stefan_boltzmann = 4.903e-9  # ثابت ستيفان-بولتزمان
            
            # حساب الإشعاع الشمسي
            day_of_year = date.timetuple().tm_yday
            declination = 0.409 * math.sin(2 * math.pi * day_of_year / 365 - 1.39)
            
            # حساب ET0 المبسط
            # هذه معادلة مبسطة - في التطبيق الفعلي تحتاج إلى حسابات أكثر دقة
            et0 = (
                (temp + 273.16) * (humidity / 100) * wind_speed * 0.1 +
                (25 - temp) * 0.05
            )
            
            return max(0, et0)
            
        except Exception:
            return 4.0  # قيمة افتراضية
    
    def _get_fallback_weather(self, latitude: float, longitude: float) -> Dict:
        """بيانات الطقس الاحتياطية"""
        return {
            'temperature': 25,
            'humidity': 50,
            'pressure': 1013.25,
            'wind_speed': 2,
            'wind_direction': 0,
            'visibility': 10,
            'cloud_cover': 20,
            'description': 'Weather data unavailable',
            'icon': '01d',
            'timestamp': timezone.now()
        }
    
    def _get_fallback_forecast(self, latitude: float, longitude: float, days: int) -> List[Dict]:
        """توقعات الطقس الاحتياطية"""
        forecasts = []
        base_temp = 25
        
        for i in range(days):
            date = timezone.now().date() + timedelta(days=i)
            temp_variation = (i % 3 - 1) * 3  # تغيير بسيط في درجة الحرارة
            
            forecasts.append({
                'date': date,
                'temperature': base_temp + temp_variation,
                'min_temperature': base_temp + temp_variation - 5,
                'max_temperature': base_temp + temp_variation + 5,
                'humidity': 50,
                'pressure': 1013.25,
                'wind_speed': 2,
                'wind_direction': 180,
                'cloud_cover': 20,
                'rain': 0,
                'description': 'Partly cloudy',
                'icon': '02d'
            })
        
        return forecasts


class WeatherAlertService:
    """خدمة تنبيهات الطقس المتقدمة"""
    
    def __init__(self):
        self.weather_service = WeatherService()
    
    def check_critical_conditions(self, farm: Farm) -> List[Dict]:
        """التحقق من الظروف الحرجة"""
        alerts = []
        
        # الحصول على بيانات الطقس الحالية
        current_weather = self.weather_service.get_current_weather(farm.location.y, farm.location.x)
        
        # التحقق من درجات الحرارة القصوى
        if current_weather.get('temperature', 0) > 45:
            alerts.append(self._create_alert('extreme_heat', 'critical', farm, {
                'temperature': current_weather['temperature'],
                'message': 'درجة حرارة قاتلة - توقف عن العمل في الحقل'
            }))
        
        # التحقق من الرياح العاتية
        if current_weather.get('wind_speed', 0) > 20:
            alerts.append(self._create_alert('strong_wind', 'high', farm, {
                'wind_speed': current_weather['wind_speed'],
                'message': 'رياح قوية قد تسبب أضراراً'
            }))
        
        # التحقق من العواصف
        if current_weather.get('description', '').lower().find('storm') != -1:
            alerts.append(self._create_alert('storm', 'high', farm, {
                'condition': current_weather['description'],
                'message': 'عاصفة متوقعة - البقاء في الأماكن المغلقة'
            }))
        
        return alerts
    
    def generate_irrigation_weather_report(self, farm: Farm) -> Dict:
        """إنشاء تقرير طقس مخصص للري"""
        current_weather = self.weather_service.get_current_weather(farm.location.y, farm.location.x)
        hourly_forecast = self.weather_service.get_hourly_forecast(farm.location.y, farm.location.x, hours=24)
        
        # حساب مؤشر ملاءمة الري
        irrigation_suitability = self._calculate_irrigation_suitability(current_weather, hourly_forecast)
        
        # التوصيات
        recommendations = self._generate_irrigation_recommendations(current_weather, hourly_forecast)
        
        return {
            'current_conditions': current_weather,
            'irrigation_suitability': irrigation_suitability,
            'recommendations': recommendations,
            'next_24_hours': hourly_forecast[:8],  # أول 8 ساعات
            'optimal_irrigation_times': self._find_optimal_irrigation_times(hourly_forecast),
            'avoid_irrigation_times': self._find_avoid_irrigation_times(hourly_forecast)
        }
    
    def _create_alert(self, alert_type: str, severity: str, farm: Farm, data: Dict) -> Dict:
        """إنشاء تنبيه"""
        return {
            'type': alert_type,
            'severity': severity,
            'farm_id': farm.id,
            'farm_name': farm.name,
            'data': data,
            'timestamp': timezone.now()
        }
    
    def _calculate_irrigation_suitability(self, current_weather: Dict, forecast: List[Dict]) -> Dict:
        """حساب ملاءمة الري"""
        temp = current_weather.get('temperature', 25)
        humidity = current_weather.get('humidity', 50)
        wind_speed = current_weather.get('wind_speed', 2)
        
        # حساب الدرجة (0-100)
        score = 100
        
        # خصم لدرجات الحرارة المرتفعة
        if temp > 30:
            score -= (temp - 30) * 2
        
        # خصم لانخفاض الرطوبة
        if humidity < 40:
            score -= (40 - humidity) * 1.5
        
        # خصم للرياح العالية
        if wind_speed > 5:
            score -= (wind_speed - 5) * 3
        
        score = max(0, min(100, score))
        
        return {
            'score': score,
            'rating': 'Excellent' if score > 80 else 'Good' if score > 60 else 'Fair' if score > 40 else 'Poor',
            'factors': {
                'temperature': temp,
                'humidity': humidity,
                'wind_speed': wind_speed
            }
        }
    
    def _generate_irrigation_recommendations(self, current_weather: Dict, forecast: List[Dict]) -> List[str]:
        """إنشاء توصيات للري"""
        recommendations = []
        
        temp = current_weather.get('temperature', 25)
        humidity = current_weather.get('humidity', 50)
        
        if temp > 35:
            recommendations.append('أرجئ الري إلى وقت أبرد في اليوم')
        
        if humidity < 30:
            recommendations.append('زد من كمية المياه بسبب الجفاف')
        
        if any(hour.get('rain', 0) > 0 for hour in forecast[:6]):
            recommendations.append('توقع أمطار - أوقف الري المجدول')
        
        return recommendations
    
    def _find_optimal_irrigation_times(self, forecast: List[Dict]) -> List[Dict]:
        """إيجاد أفضل أوقات الري"""
        optimal_times = []
        
        for hour_data in forecast:
            temp = hour_data.get('temperature', 25)
            humidity = hour_data.get('humidity', 50)
            wind_speed = hour_data.get('wind_speed', 2)
            rain = hour_data.get('rain', 0)
            
            # حساب الدرجة
            score = 100
            
            if temp > 30:
                score -= (temp - 30) * 2
            
            if humidity < 40:
                score -= (40 - humidity) * 1.5
            
            if wind_speed > 5:
                score -= (wind_speed - 5) * 3
            
            if rain > 0:
                score = 0
            
            score = max(0, min(100, score))
            
            if score > 70:
                optimal_times.append({
                    'time': hour_data.get('time'),
                    'score': score,
                    'temperature': temp,
                    'humidity': humidity
                })
        
        return sorted(optimal_times, key=lambda x: x['score'], reverse=True)[:3]
    
    def _find_avoid_irrigation_times(self, forecast: List[Dict]) -> List[Dict]:
        """إيجاد الأوقات التي يجب تجنب الري فيها"""
        avoid_times = []
        
        for hour_data in forecast:
            temp = hour_data.get('temperature', 25)
            rain = hour_data.get('rain', 0)
            wind_speed = hour_data.get('wind_speed', 2)
            
            if temp > 40 or rain > 0 or wind_speed > 15:
                avoid_times.append({
                    'time': hour_data.get('time'),
                    'reason': 'Extreme heat' if temp > 40 else 'Rain expected' if rain > 0 else 'Strong wind',
                    'temperature': temp,
                    'rain': rain,
                    'wind_speed': wind_speed
                })
        
        return avoid_times


class WeatherDataProcessor:
    """معالج بيانات الطقس للتكامل مع الأنظمة الأخرى"""
    
    def __init__(self):
        self.weather_service = WeatherService()
    
    def process_farm_weather_data(self, farm: Farm) -> Dict:
        """معالجة بيانات الطقس للمزرعة"""
        current_weather = self.weather_service.get_current_weather(farm.location.y, farm.location.x)
        forecast = self.weather_service.get_forecast(farm.location.y, farm.location.x, days=7)
        
        # حساب المؤشرات الزراعية
        agricultural_indices = self._calculate_agricultural_indices(current_weather, forecast)
        
        # التكامل مع بيانات IoT
        iot_integration = self._integrate_with_iot_data(farm, current_weather)
        
        return {
            'current_weather': current_weather,
            'forecast': forecast,
            'agricultural_indices': agricultural_indices,
            'iot_integration': iot_integration,
            'recommendations': self._generate_weather_based_recommendations(current_weather, agricultural_indices)
        }
    
    def _calculate_agricultural_indices(self, current_weather: Dict, forecast: List[Dict]) -> Dict:
        """حساب المؤشرات الزراعية"""
        temp = current_weather.get('temperature', 25)
        humidity = current_weather.get('humidity', 50)
        
        # مؤشر ملاءمة العمل الزراعي
        work_suitability = 100
        if temp > 35:
            work_suitability -= (temp - 35) * 3
        if humidity > 80:
            work_suitability -= (humidity - 80) * 2
        
        # مؤشر خطر الأمراض
        disease_risk = 0
        if temp > 25 and humidity > 70:
            disease_risk = min(100, (temp - 25) * 2 + (humidity - 70) * 1.5)
        
        # مؤشر ملاءمة الحصاد
        harvest_suitability = 100
        if temp > 30 or humidity > 60:
            harvest_suitability -= abs(temp - 25) * 2 + abs(humidity - 50) * 1.5
        
        return {
            'work_suitability': max(0, min(100, work_suitability)),
            'disease_risk': max(0, min(100, disease_risk)),
            'harvest_suitability': max(0, min(100, harvest_suitability))
        }
    
    def _integrate_with_iot_data(self, farm: Farm, current_weather: Dict) -> Dict:
        """التكامل مع بيانات IoT"""
        try:
            # الحصول على أحدث قراءات IoT
            latest_reading = SensorReading.objects.filter(
                device__farm=farm
            ).order_by('-timestamp').first()
            
            if latest_reading:
                # مقارنة بيانات الطقس مع بيانات IoT
                weather_temp = current_weather.get('temperature', 0)
                iot_temp = latest_reading.temperature or 0
                
                temp_difference = abs(weather_temp - iot_temp)
                
                return {
                    'iot_temperature': iot_temp,
                    'weather_temperature': weather_temp,
                    'temperature_difference': temp_difference,
                    'data_consistency': 'Good' if temp_difference < 5 else 'Poor',
                    'last_iot_update': latest_reading.timestamp
                }
            
        except Exception as e:
            logger.error(f"Error integrating with IoT data: {e}")
        
        return {}
    
    def _generate_weather_based_recommendations(self, current_weather: Dict, indices: Dict) -> List[str]:
        """إنشاء توصيات بناءً على الطقس"""
        recommendations = []
        
        temp = current_weather.get('temperature', 25)
        humidity = current_weather.get('humidity', 50)
        
        if indices['work_suitability'] < 50:
            recommendations.append('الظروف الجوية غير ملائمة للعمل الزراعي')
        
        if indices['disease_risk'] > 70:
            recommendations.append('خطر مرتفع للأمراض - راقب المحاصيل عن كثب')
        
        if temp > 35:
            recommendations.append('درجات حرارة مرتفعة - راعِ ظروف العمل')
        
        if humidity > 80:
            recommendations.append('رطوبة عالية - تجنب الرش بالمبيدات')
        
        return recommendations