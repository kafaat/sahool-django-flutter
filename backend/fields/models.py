"""
Models for fields app.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Field(models.Model):
    """
    Field model.
    """

    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='fields', verbose_name=_('المزرعة'))
    name = models.CharField(max_length=200, verbose_name=_('اسم الحقل'))
    area = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('المساحة (هكتار)'))
    soil_type = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('نوع التربة'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التحديث'))

    class Meta:
        verbose_name = _('Field')
        verbose_name_plural = _('Fields')
        ordering = ['-created_at']

    def __str__(self):
        return self.name


