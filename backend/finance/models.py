"""
نماذج المالية والمحاسبة - التكامل الشامل
Finance and Accounting Models - Comprehensive Integration
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Avg
from decimal import Decimal

from apps.core.models import BaseModel
from apps.farms.models import Farm, Crop
from apps.users.models import User


class Account(BaseModel):
    """نموذج الحسابات المالية"""
    
    ACCOUNT_TYPES = [
        ('asset', 'أصل'),
        ('liability', 'خصم'),
        ('equity', 'حقوق ملكية'),
        ('revenue', 'إيرادات'),
        ('expense', 'مصاريف'),
    ]
    
    ACCOUNT_CATEGORIES = [
        ('cash', 'نقدية'),
        ('bank', 'بنك'),
        ('accounts_receivable', 'ذمم مدينة'),
        ('accounts_payable', 'ذمم دائنة'),
        ('inventory', 'مخزون'),
        ('equipment', 'معدات'),
        ('land', 'أرض'),
        ('buildings', 'مباني'),
        ('loans', 'قروض'),
        ('taxes', 'ضرائب'),
        ('salaries', 'رواتب'),
        ('utilities', 'خدمات'),
        ('seeds', 'بذور'),
        ('fertilizers', 'أسمدة'),
        ('pesticides', 'مبيدات'),
        ('fuel', 'وقود'),
        ('maintenance', 'صيانة'),
        ('sales', 'مبيعات'),
        ('other_income', 'إيرادات أخرى'),
        ('other_expense', 'مصاريف أخرى'),
    ]
    
    name = models.CharField(max_length=255, verbose_name='اسم الحساب')
    code = models.CharField(max_length=20, unique=True, verbose_name='كود الحساب')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, verbose_name='نوع الحساب')
    category = models.CharField(max_length=30, choices=ACCOUNT_CATEGORIES, verbose_name='الفئة')
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='accounts', verbose_name='المزرعة')
    parent_account = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_accounts', verbose_name='الحساب الرئيسي')
    
    # الرصيد
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='الرصيد الحالي')
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='الرصيد الافتتاحي')
    
    # الإعدادات
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    is_system_account = models.BooleanField(default=False, verbose_name='حساب نظام')
    
    # الملاحظات
    description = models.TextField(blank=True, verbose_name='الوصف')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    class Meta:
        db_table = 'accounts'
        verbose_name = 'حساب'
        verbose_name_plural = 'الحسابات'
        ordering = ['code', 'name']
        indexes = [
            models.Index(fields=['farm', 'account_type']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def update_balance(self):
        """تحديث الرصيد الحالي"""
        credit_total = self.journal_entries.filter(transaction_type='credit').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        debit_total = self.journal_entries.filter(transaction_type='debit').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        if self.account_type in ['asset', 'expense']:
            self.current_balance = self.opening_balance + debit_total - credit_total
        else:  # liability, equity, revenue
            self.current_balance = self.opening_balance + credit_total - debit_total
        
        self.save(update_fields=['current_balance'])
    
    def get_balance_at_date(self, date):
        """الحصول على الرصيد في تاريخ معين"""
        entries = self.journal_entries.filter(created_at__lte=date)
        
        credit_total = entries.filter(transaction_type='credit').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        debit_total = entries.filter(transaction_type='debit').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        if self.account_type in ['asset', 'expense']:
            return self.opening_balance + debit_total - credit_total
        else:
            return self.opening_balance + credit_total - debit_total


class Transaction(BaseModel):
    """نموذج المعاملات المالية"""
    
    TRANSACTION_TYPES = [
        ('income', 'إيراد'),
        ('expense', 'مصروف'),
        ('transfer', 'تحويل'),
        ('adjustment', 'تسوية'),
        ('opening_balance', 'رصيد افتتاحي'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'نقدي'),
        ('bank_transfer', 'تحويل بنكي'),
        ('check', 'شيك'),
        ('credit_card', 'بطاقة ائتمان'),
        ('debit_card', 'بطاقة خصم'),
        ('mobile_payment', 'دفع إلكتروني'),
        ('other', 'أخرى'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'معلق'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
        ('refunded', 'مُسترجع'),
    ]
    
    transaction_number = models.CharField(max_length=50, unique=True, verbose_name='رقم المعاملة')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name='نوع المعاملة')
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='transactions', verbose_name='المزرعة')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, null=True, blank=True, related_name='transactions', verbose_name='المحصول')
    
    # التفاصيل
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='المبلغ')
    currency = models.CharField(max_length=10, default='YER', verbose_name='العملة')
    
    # التاريخ
    transaction_date = models.DateField(verbose_name='تاريخ المعاملة')
    due_date = models.DateField(null=True, blank=True, verbose_name='تاريخ الاستحقاق')
    
    # طريقة الدفع
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, verbose_name='طريقة الدفع')
    
    # المراجع
    reference_number = models.CharField(max_length=100, blank=True, verbose_name='رقم المرجع')
    invoice_number = models.CharField(max_length=100, blank=True, verbose_name='رقم الفاتورة')
    
    # الأطراف
    payee = models.CharField(max_length=255, blank=True, verbose_name='المستفيد')
    payer = models.CharField(max_length=255, blank=True, verbose_name='الدافع')
    
    # الحالة
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    
    # التصنيف
    category = models.CharField(max_length=50, verbose_name='التصنيف')
    subcategory = models.CharField(max_length=50, blank=True, verbose_name='التصنيف الفرعي')
    
    # الملاحظات
    description = models.TextField(verbose_name='الوصف')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    # المرفقات
    has_attachments = models.BooleanField(default=False, verbose_name='لديه مرفقات')
    
    # المستخدم
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_transactions', verbose_name='أنشأ بواسطة')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_transactions', verbose_name='اعتمد بواسطة')
    
    class Meta:
        db_table = 'transactions'
        verbose_name = 'معاملة'
        verbose_name_plural = 'المعاملات'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['farm', 'transaction_date']),
            models.Index(fields=['transaction_type', 'status']),
            models.Index(fields=['category', 'subcategory']),
        ]
    
    def __str__(self):
        return f"{self.transaction_number} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_number:
            self.transaction_number = self._generate_transaction_number()
        super().save(*args, **kwargs)
    
    def _generate_transaction_number(self):
        """توليد رقم معاملة فريد"""
        prefix = 'TRX'
        date_str = timezone.now().strftime('%Y%m%d')
        count = Transaction.objects.filter(created_at__date=timezone.now().date()).count() + 1
        return f"{prefix}{date_str}{count:06d}"
    
    def approve(self, user):
        """اعتماد المعاملة"""
        self.status = 'completed'
        self.approved_by = user
        self.save(update_fields=['status', 'approved_by'])
    
    def cancel(self, reason=None):
        """إلغاء المعاملة"""
        self.status = 'cancelled'
        if reason:
            self.notes += f"\nسبب الإلغاء: {reason}"
        self.save(update_fields=['status', 'notes'])


class JournalEntry(BaseModel):
    """نموذج القيود اليومية"""
    
    ENTRY_TYPES = [
        ('debit', 'مدين'),
        ('credit', 'دائن'),
    ]
    
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='journal_entries', verbose_name='المعاملة')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='journal_entries', verbose_name='الحساب')
    
    transaction_type = models.CharField(max_length=10, choices=ENTRY_TYPES, verbose_name='نوع القيد')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='المبلغ')
    
    # الوصف
    description = models.TextField(blank=True, verbose_name='الوصف')
    
    # التاريخ
    entry_date = models.DateField(verbose_name='تاريخ القيد')
    
    class Meta:
        db_table = 'journal_entries'
        verbose_name = 'قيد يومي'
        verbose_name_plural = 'القيود اليومية'
        ordering = ['-entry_date', '-created_at']
        indexes = [
            models.Index(fields=['transaction', 'account']),
            models.Index(fields=['account', 'entry_date']),
            models.Index(fields=['transaction_type', 'amount']),
        ]
    
    def __str__(self):
        return f"{self.account.name} - {self.transaction_type} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.entry_date:
            self.entry_date = self.transaction.transaction_date
        super().save(*args, **kwargs)
        
        # تحديث رصيد الحساب
        self.account.update_balance()


class Budget(BaseModel):
    """نموذج الميزانيات"""
    
    BUDGET_TYPES = [
        ('annual', 'سنوي'),
        ('quarterly', 'ربع سنوي'),
        ('monthly', 'شهري'),
        ('project', 'مشروع'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('approved', 'معتمد'),
        ('active', 'نشط'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]
    
    name = models.CharField(max_length=255, verbose_name='اسم الميزانية')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='budgets', verbose_name='المزرعة')
    
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPES, verbose_name='نوع الميزانية')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='الحالة')
    
    # الفترة
    start_date = models.DateField(verbose_name='تاريخ البدء')
    end_date = models.DateField(verbose_name='تاريخ الانتهاء')
    
    # الميزانية الكلية
    total_budget = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='الميزانية الكلية')
    
    # المستخدم
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_budgets', verbose_name='أنشأ بواسطة')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_budgets', verbose_name='اعتمد بواسطة')
    
    # الملاحظات
    description = models.TextField(blank=True, verbose_name='الوصف')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    class Meta:
        db_table = 'budgets'
        verbose_name = 'ميزانية'
        verbose_name_plural = 'الميزانيات'
        ordering = ['-start_date', '-created_at']
        indexes = [
            models.Index(fields=['farm', 'budget_type']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.farm.name}"
    
    def approve(self, user):
        """اعتماد الميزانية"""
        self.status = 'approved'
        self.approved_by = user
        self.save(update_fields=['status', 'approved_by'])
    
    def activate(self):
        """تفعيل الميزانية"""
        self.status = 'active'
        self.save(update_fields=['status'])
    
    def get_actual_spending(self):
        """الحصول على الإنفاق الفعلي"""
        return self.budget_items.aggregate(
            total=Sum('actual_amount')
        )['total'] or 0
    
    def get_variance(self):
        """حساب الفرق بين الميزانية والفعلي"""
        actual = self.get_actual_spending()
        return self.total_budget - actual


class BudgetItem(BaseModel):
    """نموذج عناصر الميزانية"""
    
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='budget_items', verbose_name='الميزانية')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='budget_items', verbose_name='الحساب')
    
    # الميزانية المخططة
    budgeted_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='المبلغ الميزاني')
    
    # الفعلي
    actual_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='المبلغ الفعلي')
    
    # التواريخ
    planned_date = models.DateField(verbose_name='التاريخ المخطط')
    actual_date = models.DateField(null=True, blank=True, verbose_name='التاريخ الفعلي')
    
    # الحالة
    is_completed = models.BooleanField(default=False, verbose_name='مكتمل')
    
    # الملاحظات
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    class Meta:
        db_table = 'budget_items'
        verbose_name = 'عنصر ميزانية'
        verbose_name_plural = 'عناصر الميزانيات'
        ordering = ['planned_date']
        indexes = [
            models.Index(fields=['budget', 'account']),
            models.Index(fields=['planned_date', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.account.name} - {self.budgeted_amount}"
    
    def update_actual_amount(self, amount):
        """تحديث المبلغ الفعلي"""
        self.actual_amount = amount
        if amount >= self.budgeted_amount:
            self.is_completed = True
        self.save(update_fields=['actual_amount', 'is_completed'])
    
    def get_variance(self):
        """حساب الفرق"""
        return self.budgeted_amount - self.actual_amount
    
    def get_variance_percentage(self):
        """حساب نسبة الفرق"""
        if self.budgeted_amount == 0:
            return 0
        return (self.get_variance() / self.budgeted_amount) * 100


class Invoice(BaseModel):
    """نموذج الفواتير"""
    
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('sent', 'مرسلة'),
        ('viewed', 'مطلوبة'),
        ('paid', 'مدفوعة'),
        ('overdue', 'متأخرة'),
        ('cancelled', 'ملغاة'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name='رقم الفاتورة')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='invoices', verbose_name='المزرعة')
    
    # العميل
    customer_name = models.CharField(max_length=255, verbose_name='اسم العميل')
    customer_email = models.EmailField(blank=True, verbose_name='بريد العميل')
    customer_phone = models.CharField(max_length=20, blank=True, verbose_name='هاتف العميل')
    customer_address = models.TextField(blank=True, verbose_name='عنوان العميل')
    
    # التواريخ
    invoice_date = models.DateField(verbose_name='تاريخ الفاتورة')
    due_date = models.DateField(verbose_name='تاريخ الاستحقاق')
    
    # المبالغ
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='المجموع الفرعي')
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='مبلغ الضريبة')
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='مبلغ الخصم')
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='المبلغ الإجمالي')
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='المبلغ المدفوع')
    
    # الضريبة والخصم
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='نسبة الضريبة (%)')
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='نسبة الخصم (%)')
    
    # الحالة
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='الحالة')
    
    # الملاحظات
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    terms_and_conditions = models.TextField(blank=True, verbose_name='الشروط والأحكام')
    
    # الإرسال والمتابعة
    sent_date = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الإرسال')
    viewed_date = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ المشاهدة')
    paid_date = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الدفع')
    
    class Meta:
        db_table = 'invoices'
        verbose_name = 'فاتورة'
        verbose_name_plural = 'الفواتير'
        ordering = ['-invoice_date', '-created_at']
        indexes = [
            models.Index(fields=['farm', 'status']),
            models.Index(fields=['customer_name', 'status']),
            models.Index(fields=['due_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self._generate_invoice_number()
        
        # حساب المجموع
        self._calculate_totals()
        super().save(*args, **kwargs)
    
    def _generate_invoice_number(self):
        """توليد رقم فاتورة فريد"""
        prefix = 'INV'
        date_str = timezone.now().strftime('%Y%m')
        count = Invoice.objects.filter(created_at__month=timezone.now().month).count() + 1
        return f"{prefix}{date_str}{count:04d}"
    
    def _calculate_totals(self):
        """حساب المجاميع"""
        # حساب المجموع الفرعي من العناصر
        self.subtotal = self.items.aggregate(total=Sum('line_total'))['total'] or 0
        
        # حساب الخصم
        self.discount_amount = self.subtotal * (self.discount_rate / 100)
        
        # حساب الضريبة
        taxable_amount = self.subtotal - self.discount_amount
        self.tax_amount = taxable_amount * (self.tax_rate / 100)
        
        # المجموع الإجمالي
        self.total_amount = taxable_amount + self.tax_amount
    
    def mark_as_sent(self):
        """وضع علامة كمرسلة"""
        self.status = 'sent'
        self.sent_date = timezone.now()
        self.save(update_fields=['status', 'sent_date'])
    
    def mark_as_paid(self, amount=None):
        """وضع علامة كمدفوعة"""
        self.status = 'paid'
        self.paid_date = timezone.now()
        if amount:
            self.paid_amount = amount
        else:
            self.paid_amount = self.total_amount
        self.save(update_fields=['status', 'paid_date', 'paid_amount'])
    
    def get_balance_due(self):
        """الحصول على الرصيد المستحق"""
        return self.total_amount - self.paid_amount
    
    def is_overdue(self):
        """التحقق إذا كانت متأخرة"""
        return self.status != 'paid' and timezone.now().date() > self.due_date


class InvoiceItem(BaseModel):
    """نموذج عناصر الفاتورة"""
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name='الفاتورة')
    
    # المنتج/الخدمة
    item_name = models.CharField(max_length=255, verbose_name='اسم العنصر')
    item_description = models.TextField(blank=True, verbose_name='وصف العنصر')
    
    # الكمية والسعر
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='الكمية')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='سعر الوحدة')
    unit = models.CharField(max_length=50, default='piece', verbose_name='الوحدة')
    
    # الخصم
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='مبلغ الخصم')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='نسبة الخصم (%)')
    
    # الضريبة
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='نسبة الضريبة (%)')
    
    # المجاميع
    line_total = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='المجموع')
    
    class Meta:
        db_table = 'invoice_items'
        verbose_name = 'عنصر فاتورة'
        verbose_name_plural = 'عناصر الفواتير'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['invoice', 'item_name']),
        ]
    
    def __str__(self):
        return f"{self.item_name} - {self.quantity} {self.unit}"
    
    def save(self, *args, **kwargs):
        # حساب المجموع
        self._calculate_line_total()
        super().save(*args, **kwargs)
    
    def _calculate_line_total(self):
        """حساب المجموع السطري"""
        subtotal = self.quantity * self.unit_price
        
        # الخصم
        if self.discount_percentage > 0:
            self.discount_amount = subtotal * (self.discount_percentage / 100)
        
        discounted_total = subtotal - self.discount_amount
        
        # الضريبة
        tax_amount = discounted_total * (self.tax_rate / 100)
        
        # المجموع النهائي
        self.line_total = discounted_total + tax_amount


class Payment(BaseModel):
    """نموذج المدفوعات"""
    
    PAYMENT_METHODS = [
        ('cash', 'نقدي'),
        ('bank_transfer', 'تحويل بنكي'),
        ('check', 'شيك'),
        ('credit_card', 'بطاقة ائتمان'),
        ('mobile_payment', 'دفع إلكتروني'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'معلق'),
        ('completed', 'مكتمل'),
        ('failed', 'فشل'),
        ('refunded', 'مُسترجع'),
    ]
    
    payment_number = models.CharField(max_length=50, unique=True, verbose_name='رقم الدفع')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', verbose_name='الفاتورة')
    
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='المبلغ')
    currency = models.CharField(max_length=10, default='YER', verbose_name='العملة')
    
    # طريقة الدفع
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, verbose_name='طريقة الدفع')
    
    # التاريخ
    payment_date = models.DateField(verbose_name='تاريخ الدفع')
    
    # المراجع
    reference_number = models.CharField(max_length=100, blank=True, verbose_name='رقم المرجع')
    
    # الحالة
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    
    # الملاحظات
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    class Meta:
        db_table = 'payments'
        verbose_name = 'دفعة'
        verbose_name_plural = 'المدفوعات'
        ordering = ['-payment_date', '-created_at']
        indexes = [
            models.Index(fields=['invoice', 'status']),
            models.Index(fields=['payment_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.payment_number} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.payment_number:
            self.payment_number = self._generate_payment_number()
        super().save(*args, **kwargs)
    
    def _generate_payment_number(self):
        """توليد رقم دفعة فريد"""
        prefix = 'PAY'
        date_str = timezone.now().strftime('%Y%m%d')
        count = Payment.objects.filter(created_at__date=timezone.now().date()).count() + 1
        return f"{prefix}{date_str}{count:04d}"
    
    def complete(self):
        """إكمال الدفعة"""
        self.status = 'completed'
        self.save(update_fields=['status'])
        
        # تحديث الفاتورة
        self.invoice.paid_amount += self.amount
        if self.invoice.paid_amount >= self.invoice.total_amount:
            self.invoice.status = 'paid'
        self.invoice.save(update_fields=['paid_amount', 'status'])


class FinancialReport(BaseModel):
    """نموذج التقارير المالية"""
    
    REPORT_TYPES = [
        ('income_statement', 'قائمة الدخل'),
        ('balance_sheet', 'الميزانية العمومية'),
        ('cash_flow', 'تدفقات النقدية'),
        ('budget_variance', 'تحليل انحراف الميزانية'),
        ('profit_loss', 'الربح والخسارة'),
        ('trial_balance', 'ميزان المراجعة'),
    ]
    
    name = models.CharField(max_length=255, verbose_name='اسم التقرير')
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES, verbose_name='نوع التقرير')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='financial_reports', verbose_name='المزرعة')
    
    # الفترة
    start_date = models.DateField(verbose_name='تاريخ البدء')
    end_date = models.DateField(verbose_name='تاريخ الانتهاء')
    
    # البيانات
    report_data = models.JSONField(default=dict, verbose_name='بيانات التقرير')
    summary = models.TextField(blank=True, verbose_name='ملخص التقرير')
    
    # الملف
    file_path = models.CharField(max_length=500, blank=True, verbose_name='مسار الملف')
    file_format = models.CharField(max_length=10, default='pdf', verbose_name='صيغة الملف')
    
    # المستخدم
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports', verbose_name='أنشأ بواسطة')
    
    class Meta:
        db_table = 'financial_reports'
        verbose_name = 'تقرير مالي'
        verbose_name_plural = 'التقارير المالية'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['farm', 'report_type']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['generated_by']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.farm.name}"


class TaxRecord(BaseModel):
    """نموذج السجلات الضريبية"""
    
    TAX_TYPES = [
        ('income_tax', 'ضريبة الدخل'),
        ('sales_tax', 'ضريبة المبيعات'),
        ('property_tax', 'ضريبة العقار'),
        ('payroll_tax', 'ضريبة الرواتب'),
        ('customs_tax', 'ضريبة الجمارك'),
        ('other', 'أخرى'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'معلق'),
        ('filed', 'مقدم'),
        ('paid', 'مدفوع'),
        ('overdue', 'متأخر'),
        ('disputed', 'متنازع عليه'),
    ]
    
    tax_type = models.CharField(max_length=20, choices=TAX_TYPES, verbose_name='نوع الضريبة')
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='tax_records', verbose_name='المزرعة')
    
    # الفترة
    tax_year = models.PositiveIntegerField(verbose_name='السنة الضريبية')
    tax_period_start = models.DateField(verbose_name='بداية الفترة الضريبية')
    tax_period_end = models.DateField(verbose_name='نهاية الفترة الضريبية')
    
    # المبالغ
    taxable_income = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='الدخل الخاضع للضريبة')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='نسبة الضريبة (%)')
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='مبلغ الضريبة')
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='المبلغ المدفوع')
    
    # الحالة
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    
    # التواريخ
    filing_date = models.DateField(null=True, blank=True, verbose_name='تاريخ التقديم')
    due_date = models.DateField(verbose_name='تاريخ الاستحقاق')
    payment_date = models.DateField(null=True, blank=True, verbose_name='تاريخ الدفع')
    
    # المراجع
    tax_reference = models.CharField(max_length=100, blank=True, verbose_name='المرجع الضريبي')
    
    # الملاحظات
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    class Meta:
        db_table = 'tax_records'
        verbose_name = 'سجل ضريبي'
        verbose_name_plural = 'السجلات الضريبية'
        ordering = ['-tax_year', '-created_at']
        indexes = [
            models.Index(fields=['farm', 'tax_year']),
            models.Index(fields=['tax_type', 'status']),
            models.Index(fields=['due_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_tax_type_display()} - {self.farm.name} - {self.tax_year}"
    
    def get_tax_due(self):
        """الحصول على الضريبة المستحقة"""
        return self.tax_amount - self.paid_amount
    
    def is_overdue(self):
        """التحقق إذا كانت متأخرة"""
        return self.status != 'paid' and timezone.now().date() > self.due_date