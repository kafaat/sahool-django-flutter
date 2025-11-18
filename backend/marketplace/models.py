"""
نماذج نظام Marketplace لتجارة المحاصيل
"""
from django.db import models
from django.core.validators import MinValueValidator
from users.models import User
from farms.models import Crop


class CropListing(models.Model):
    """
    إعلان بيع محصول
    """
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('sold', 'مباع'),
        ('expired', 'منتهي'),
        ('cancelled', 'ملغي'),
    ]
    
    QUALITY_CHOICES = [
        ('premium', 'ممتاز'),
        ('grade_a', 'درجة أولى'),
        ('grade_b', 'درجة ثانية'),
        ('standard', 'عادي'),
    ]
    
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='crop_listings',
        verbose_name='البائع'
    )
    
    crop = models.ForeignKey(
        Crop,
        on_delete=models.CASCADE,
        related_name='listings',
        verbose_name='المحصول',
        null=True,
        blank=True
    )
    
    title = models.CharField('العنوان', max_length=200)
    description = models.TextField('الوصف')
    
    crop_type = models.CharField('نوع المحصول', max_length=100)
    quantity = models.DecimalField(
        'الكمية (كجم)',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    price_per_kg = models.DecimalField(
        'السعر لكل كجم',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    quality_grade = models.CharField(
        'درجة الجودة',
        max_length=20,
        choices=QUALITY_CHOICES,
        default='standard'
    )
    
    available_date = models.DateField('تاريخ التوفر')
    expiry_date = models.DateField('تاريخ الانتهاء', null=True, blank=True)
    
    location = models.CharField('الموقع', max_length=200)
    latitude = models.DecimalField(
        'خط العرض',
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        'خط الطول',
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    
    status = models.CharField(
        'الحالة',
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    images = models.JSONField('الصور', default=list, blank=True)
    
    views_count = models.IntegerField('عدد المشاهدات', default=0)
    
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at = models.DateTimeField('تاريخ التحديث', auto_now=True)
    
    class Meta:
        db_table = 'marketplace_listings'
        verbose_name = 'إعلان محصول'
        verbose_name_plural = 'إعلانات المحاصيل'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['crop_type']),
            models.Index(fields=['seller']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.seller.username}"
    
    @property
    def total_price(self):
        """السعر الإجمالي"""
        return self.quantity * self.price_per_kg


class Offer(models.Model):
    """
    عرض شراء على إعلان
    """
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('accepted', 'مقبول'),
        ('rejected', 'مرفوض'),
        ('cancelled', 'ملغي'),
    ]
    
    listing = models.ForeignKey(
        CropListing,
        on_delete=models.CASCADE,
        related_name='offers',
        verbose_name='الإعلان'
    )
    
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='offers_made',
        verbose_name='المشتري'
    )
    
    quantity = models.DecimalField(
        'الكمية المطلوبة (كجم)',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    offered_price_per_kg = models.DecimalField(
        'السعر المعروض لكل كجم',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    message = models.TextField('رسالة', blank=True)
    
    status = models.CharField(
        'الحالة',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    created_at = models.DateTimeField('تاريخ العرض', auto_now_add=True)
    updated_at = models.DateTimeField('تاريخ التحديث', auto_now=True)
    
    class Meta:
        db_table = 'marketplace_offers'
        verbose_name = 'عرض شراء'
        verbose_name_plural = 'عروض الشراء'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['listing', 'status']),
            models.Index(fields=['buyer']),
        ]
    
    def __str__(self):
        return f"عرض من {self.buyer.username} على {self.listing.title}"
    
    @property
    def total_offered_price(self):
        """السعر الإجمالي المعروض"""
        return self.quantity * self.offered_price_per_kg


class Transaction(models.Model):
    """
    معاملة بيع مكتملة
    """
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('confirmed', 'مؤكد'),
        ('in_delivery', 'قيد التوصيل'),
        ('delivered', 'تم التوصيل'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
        ('disputed', 'متنازع عليه'),
    ]
    
    listing = models.ForeignKey(
        CropListing,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='الإعلان'
    )
    
    offer = models.OneToOneField(
        Offer,
        on_delete=models.CASCADE,
        related_name='transaction',
        verbose_name='العرض',
        null=True,
        blank=True
    )
    
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sales',
        verbose_name='البائع'
    )
    
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='purchases',
        verbose_name='المشتري'
    )
    
    quantity = models.DecimalField(
        'الكمية',
        max_digits=10,
        decimal_places=2
    )
    
    price_per_kg = models.DecimalField(
        'السعر لكل كجم',
        max_digits=10,
        decimal_places=2
    )
    
    total_amount = models.DecimalField(
        'المبلغ الإجمالي',
        max_digits=12,
        decimal_places=2
    )
    
    status = models.CharField(
        'الحالة',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    delivery_address = models.TextField('عنوان التوصيل', blank=True)
    delivery_date = models.DateField('تاريخ التوصيل', null=True, blank=True)
    
    notes = models.TextField('ملاحظات', blank=True)
    
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at = models.DateTimeField('تاريخ التحديث', auto_now=True)
    completed_at = models.DateTimeField('تاريخ الإكمال', null=True, blank=True)
    
    class Meta:
        db_table = 'marketplace_transactions'
        verbose_name = 'معاملة'
        verbose_name_plural = 'المعاملات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"معاملة #{self.id} - {self.seller.username} → {self.buyer.username}"


class Review(models.Model):
    """
    تقييم للبائع أو المشتري
    """
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='المعاملة'
    )
    
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_given',
        verbose_name='المقيّم'
    )
    
    reviewed_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_received',
        verbose_name='المستخدم المقيّم'
    )
    
    rating = models.IntegerField(
        'التقييم',
        validators=[MinValueValidator(1), MinValueValidator(5)]
    )
    
    comment = models.TextField('التعليق', blank=True)
    
    created_at = models.DateTimeField('تاريخ التقييم', auto_now_add=True)
    
    class Meta:
        db_table = 'marketplace_reviews'
        verbose_name = 'تقييم'
        verbose_name_plural = 'التقييمات'
        ordering = ['-created_at']
        unique_together = ['transaction', 'reviewer']
        indexes = [
            models.Index(fields=['reviewed_user', '-created_at']),
        ]
    
    def __str__(self):
        return f"تقييم {self.rating}⭐ من {self.reviewer.username} لـ {self.reviewed_user.username}"
