"""
Models for marketplace app.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Product(models.Model):
    """
    Product model.
    """

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products', verbose_name=_('البائع'))
    name = models.CharField(max_length=200, verbose_name=_('اسم المنتج'))
    description = models.TextField(verbose_name=_('الوصف'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('السعر'))
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('الكمية'))
    unit = models.CharField(max_length=50, verbose_name=_('الوحدة'))
    status = models.CharField(max_length=20, default='available', verbose_name=_('الحالة'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التحديث'))

    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-created_at']

    def __str__(self):
        return self.name


