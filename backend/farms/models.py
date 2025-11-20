"""
Models for farms app.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Farm(models.Model):
    """
    Farm model.
    """

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='farms', verbose_name=_('المالك'))
    name = models.CharField(max_length=200, verbose_name=_('اسم المزرعة'))
    location = models.CharField(max_length=500, verbose_name=_('الموقع'))
    area = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('المساحة (هكتار)'))
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_('خط العرض'))
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_('خط الطول'))
    description = models.TextField(blank=True, null=True, verbose_name=_('الوصف'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التحديث'))

    class Meta:
        verbose_name = _('Farm')
        verbose_name_plural = _('Farms')
        ordering = ['-created_at']

    def __str__(self):
        return self.name


