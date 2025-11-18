from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """نموذج المستخدم المخصص"""
    
    USER_TYPES = (
        ('farmer', 'مزارع صغير'),
        ('medium_farmer', 'مزارع متوسط'),
        ('company', 'شركة'),
        ('government', 'جهة حكومية'),
        ('agent', 'وكيل'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='farmer')
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=255, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    subscription_plan = models.CharField(max_length=20, default='free')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
    
    def __str__(self):
        return self.username
