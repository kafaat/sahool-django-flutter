"""
Models for irrigation app.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class IrrigationSchedule(models.Model):
    """
    IrrigationSchedule model.
    """

    field = models.ForeignKey('fields.Field', on_delete=models.CASCADE, related_name='irrigation_schedules', verbose_name=_('الحقل'))
    start_time = models.DateTimeField(verbose_name=_('وقت البدء'))
    duration_minutes = models.IntegerField(verbose_name=_('المدة (دقائق)'))
    water_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('كمية المياه (لتر)'))
    status = models.CharField(max_length=20, default='scheduled', verbose_name=_('الحالة'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))

    class Meta:
        verbose_name = _('IrrigationSchedule')
        verbose_name_plural = _('IrrigationSchedules')
        ordering = ['-created_at']

    def __str__(self):
        return f"{IrrigationSchedule} {self.pk}"


