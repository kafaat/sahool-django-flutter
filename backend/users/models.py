"""
User models for Sahool Smart Agriculture Platform.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    """
    
    USER_TYPE_CHOICES = [
        ('farmer', _('مزارع')),
        ('company', _('شركة زراعية')),
        ('government', _('جهة حكومية')),
        ('researcher', _('باحث')),
    ]
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='farmer',
        verbose_name=_('نوع المستخدم')
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('رقم الهاتف')
    )
    
    profile_image = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
        verbose_name=_('صورة الملف الشخصي')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('تاريخ التحديث')
    )
    
    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمون')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.username
