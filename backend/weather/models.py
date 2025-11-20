"""
Models for weather app.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class WeatherData(models.Model):
    """
    WeatherData model.
    """

    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='weather_data', verbose_name=_('المزرعة'))
    date = models.DateField(verbose_name=_('التاريخ'))
    temperature_max = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('درجة الحرارة العظمى'))
    temperature_min = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('درجة الحرارة الصغرى'))
    humidity = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('الرطوبة'))
    rainfall = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name=_('الأمطار (ملم)'))
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('سرعة الرياح'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))

    class Meta:
        verbose_name = _('WeatherData')
        verbose_name_plural = _('WeatherDatas')
        ordering = ['-created_at']

    def __str__(self):
        return f"{WeatherData} {self.pk}"


