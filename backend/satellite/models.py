"""
Models for satellite app.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class SatelliteImage(models.Model):
    """
    SatelliteImage model.
    """

    field = models.ForeignKey('fields.Field', on_delete=models.CASCADE, related_name='satellite_images', verbose_name=_('الحقل'))
    image_date = models.DateField(verbose_name=_('تاريخ الصورة'))
    ndvi_value = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True, verbose_name=_('قيمة NDVI'))
    image_url = models.URLField(blank=True, null=True, verbose_name=_('رابط الصورة'))
    analysis = models.TextField(blank=True, null=True, verbose_name=_('التحليل'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))

    class Meta:
        verbose_name = _('SatelliteImage')
        verbose_name_plural = _('SatelliteImages')
        ordering = ['-created_at']

    def __str__(self):
        return f"{SatelliteImage} {self.pk}"


