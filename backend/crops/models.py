"""
Models for crops app.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Crop(models.Model):
    """
    Crop model.
    """

    field = models.ForeignKey('fields.Field', on_delete=models.CASCADE, related_name='crops', verbose_name=_('الحقل'))
    name = models.CharField(max_length=200, verbose_name=_('اسم المحصول'))
    variety = models.CharField(max_length=200, blank=True, null=True, verbose_name=_('الصنف'))
    planting_date = models.DateField(verbose_name=_('تاريخ الزراعة'))
    expected_harvest_date = models.DateField(null=True, blank=True, verbose_name=_('تاريخ الحصاد المتوقع'))
    actual_harvest_date = models.DateField(null=True, blank=True, verbose_name=_('تاريخ الحصاد الفعلي'))
    status = models.CharField(max_length=50, default='growing', verbose_name=_('الحالة'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التحديث'))

    class Meta:
        verbose_name = _('Crop')
        verbose_name_plural = _('Crops')
        ordering = ['-created_at']

    def __str__(self):
        return self.name


