from django.db import models
from django.conf import settings

class Farm(models.Model):
    """نموذج المزرعة"""
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='farms')
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    total_area = models.DecimalField(max_digits=10, decimal_places=2, help_text='المساحة بالهكتار')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='farms/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'مزرعة'
        verbose_name_plural = 'المزارع'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Crop(models.Model):
    """نموذج المحصول"""
    name = models.CharField(max_length=100)
    scientific_name = models.CharField(max_length=150, blank=True)
    category = models.CharField(max_length=50)
    growing_season = models.CharField(max_length=50)
    water_requirements = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='crops/', blank=True, null=True)
    
    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'المحاصيل'
    
    def __str__(self):
        return self.name
