"""
Models for finance app.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Transaction(models.Model):
    """
    Transaction model.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions', verbose_name=_('المستخدم'))
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='transactions', null=True, blank=True, verbose_name=_('المزرعة'))
    transaction_type = models.CharField(max_length=50, verbose_name=_('نوع المعاملة'))
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_('المبلغ'))
    description = models.TextField(blank=True, null=True, verbose_name=_('الوصف'))
    date = models.DateField(verbose_name=_('التاريخ'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))

    class Meta:
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ['-created_at']

    def __str__(self):
        return f"{Transaction} {self.pk}"


