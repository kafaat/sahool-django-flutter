"""
Models for analytics app.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class FarmAnalytics(models.Model):
    """
    FarmAnalytics model.
    """

    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='analytics', verbose_name=_('المزرعة'))
    date = models.DateField(verbose_name=_('التاريخ'))
    total_yield = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_('الإنتاج الكلي'))
    water_usage = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_('استهلاك المياه'))
    efficiency_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_('درجة الكفاءة'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))

    class Meta:
        verbose_name = _('FarmAnalytics')
        verbose_name_plural = _('FarmAnalyticss')
        ordering = ['-created_at']

    def __str__(self):
        return f"{FarmAnalytics} {self.pk}"


