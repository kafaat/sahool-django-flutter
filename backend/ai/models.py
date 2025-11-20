"""
Models for ai app.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class DiseaseDetection(models.Model):
    """
    DiseaseDetection model.
    """

    crop = models.ForeignKey('crops.Crop', on_delete=models.CASCADE, related_name='disease_detections', verbose_name=_('المحصول'))
    image = models.ImageField(upload_to='disease_images/', verbose_name=_('الصورة'))
    disease_name = models.CharField(max_length=200, blank=True, null=True, verbose_name=_('اسم المرض'))
    confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_('نسبة الثقة'))
    recommendations = models.TextField(blank=True, null=True, verbose_name=_('التوصيات'))
    detected_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الكشف'))

    class Meta:
        verbose_name = _('DiseaseDetection')
        verbose_name_plural = _('DiseaseDetections')
        ordering = ['-detected_at']

    def __str__(self):
        return f"{DiseaseDetection} {self.pk}"


