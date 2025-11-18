from django.db import models
from farms.models import Farm, Crop

class Field(models.Model):
    """نموذج الحقل"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=255)
    area = models.DecimalField(max_digits=10, decimal_places=2, help_text='المساحة بالهكتار')
    soil_type = models.CharField(max_length=100)
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True, blank=True)
    planting_date = models.DateField(null=True, blank=True)
    expected_harvest_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, default='active')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'حقل'
        verbose_name_plural = 'الحقول'
    
    def __str__(self):
        return f"{self.farm.name} - {self.name}"


class IrrigationSchedule(models.Model):
    """جدول الري"""
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='irrigation_schedules')
    scheduled_date = models.DateTimeField()
    duration_minutes = models.IntegerField()
    water_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text='كمية المياه باللتر')
    status = models.CharField(max_length=20, default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'جدول ري'
        verbose_name_plural = 'جداول الري'
        ordering = ['scheduled_date']
    
    def __str__(self):
        return f"{self.field.name} - {self.scheduled_date}"
