import datetime
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


def to_date(val):
    if val is None:
        return None
    if isinstance(val, datetime.datetime):
        return val.date()
    return val


class Discount(models.Model):
    TYPE_PERCENT = 'PERCENT'
    TYPE_FIXED = 'FIXED'

    TYPE_CHOICES = [
        (TYPE_PERCENT, 'Percentage (%)'),
        (TYPE_FIXED, 'Fixed Amount ($)'),
    ]

    code = models.CharField(max_length=50, unique=True, help_text="Promo/Coupon code (case-insensitive)")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_PERCENT)
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Percentage (e.g. 10 for 10%) or Fixed dollar discount"
    )
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField()
    is_active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum total redemptions (leave blank for unlimited)")
    times_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Discount'
        verbose_name_plural = 'Discounts'

    def clean(self):
        super().clean()
        if self.code:
            self.code = self.code.strip().upper()
        valid_from = to_date(self.valid_from)
        valid_to = to_date(self.valid_to)
        if valid_from and valid_to and valid_from > valid_to:
            raise ValidationError({'valid_to': 'Valid To date must be on or after Valid From date.'})
        if self.type == self.TYPE_PERCENT and self.value is not None:
            if self.value <= Decimal('0.00') or self.value > Decimal('100.00'):
                raise ValidationError({'value': 'Percentage discount must be between 0.01% and 100%.'})
        elif self.type == self.TYPE_FIXED and self.value is not None:
            if self.value <= Decimal('0.00'):
                raise ValidationError({'value': 'Fixed discount value must be greater than 0.'})

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.strip().upper()
        if self.valid_from:
            self.valid_from = to_date(self.valid_from)
        if self.valid_to:
            self.valid_to = to_date(self.valid_to)
        super().save(*args, **kwargs)

    def is_currently_valid(self, for_date=None):
        target_date = to_date(for_date) or timezone.localdate()
        valid_from = to_date(self.valid_from)
        valid_to = to_date(self.valid_to)
        if not self.is_active:
            return False, "Discount code is inactive."
        if valid_from and target_date < valid_from:
            return False, f"Discount code is not valid until {valid_from}."
        if valid_to and target_date > valid_to:
            return False, "Discount code has expired."
        if self.usage_limit is not None and self.times_used >= self.usage_limit:
            return False, "Discount code usage limit has been reached."
        return True, "Valid discount code."

    def calculate_discount_amount(self, subtotal):
        subtotal = Decimal(str(subtotal))
        if self.type == self.TYPE_PERCENT:
            amount = (subtotal * (self.value / Decimal('100.0'))).quantize(Decimal('0.01'))
            return min(amount, subtotal)
        else:
            return min(self.value, subtotal).quantize(Decimal('0.01'))

    def __str__(self):
        val_str = f"{self.value}%" if self.type == self.TYPE_PERCENT else f"${self.value}"
        return f"{self.code} ({val_str} off)"


class Invoice(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_SENT = 'SENT'
    STATUS_PAID = 'PAID'
    STATUS_OVERDUE = 'OVERDUE'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SENT, 'Sent / Unpaid'),
        (STATUS_PAID, 'Paid'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=60, unique=True, blank=True)
    subscription = models.ForeignKey(
        'subscriptions.Subscription',
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField()
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SENT)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date', '-id']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'

    @classmethod
    def generate_next_invoice_number(cls, year=None):
        if year is None:
            year = timezone.now().year
        prefix = f"INV-{year}-"
        last_invoice = cls.objects.filter(invoice_number__startswith=prefix).order_by('-invoice_number').first()
        if last_invoice:
            try:
                seq = int(last_invoice.invoice_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = cls.objects.filter(invoice_number__startswith=prefix).count() + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    def clean(self):
        super().clean()
        issue_date = to_date(self.issue_date)
        due_date = to_date(self.due_date)
        if issue_date and due_date and due_date < issue_date:
            raise ValidationError({'due_date': 'Due date cannot be before issue date.'})
        if self.subtotal is not None and self.subtotal < Decimal('0.00'):
            raise ValidationError({'subtotal': 'Subtotal cannot be negative.'})
        if self.discount_amount is not None and self.discount_amount < Decimal('0.00'):
            raise ValidationError({'discount_amount': 'Discount amount cannot be negative.'})
        if self.tax_amount is not None and self.tax_amount < Decimal('0.00'):
            raise ValidationError({'tax_amount': 'Tax amount cannot be negative.'})

    def save(self, *args, **kwargs):
        if self.issue_date:
            self.issue_date = to_date(self.issue_date)
        if self.due_date:
            self.due_date = to_date(self.due_date)
        if not self.invoice_number:
            issue_date = to_date(self.issue_date)
            year = issue_date.year if issue_date else timezone.now().year
            self.invoice_number = self.generate_next_invoice_number(year)
        # Ensure total is calculated correctly if not explicitly set
        if self.total is None:
            self.total = max(Decimal('0.00'), (self.subtotal or Decimal('0.00')) - (self.discount_amount or Decimal('0.00')) + (self.tax_amount or Decimal('0.00'))).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    @property
    def total_paid(self):
        successful = self.payments.filter(status=Payment.STATUS_SUCCESS)
        total_paid_agg = successful.aggregate(total=models.Sum('amount'))['total']
        return (total_paid_agg or Decimal('0.00')).quantize(Decimal('0.01'))

    @property
    def balance_due(self):
        balance = self.total - self.total_paid
        return max(Decimal('0.00'), balance).quantize(Decimal('0.01'))

    @property
    def check_overdue(self):
        due_date = to_date(self.due_date)
        if due_date and self.status in [self.STATUS_SENT, self.STATUS_DRAFT] and due_date < timezone.localdate():
            return True
        return self.status == self.STATUS_OVERDUE

    def update_payment_status(self):
        """Marks invoice as PAID if payments cover total."""
        if self.total_paid >= self.total and self.total > Decimal('0.00'):
            if self.status != self.STATUS_PAID:
                self.status = self.STATUS_PAID
                self.save(update_fields=['status', 'updated_at'])
        elif self.check_overdue and self.status not in [self.STATUS_PAID, self.STATUS_CANCELLED]:
            if self.status != self.STATUS_OVERDUE:
                self.status = self.STATUS_OVERDUE
                self.save(update_fields=['status', 'updated_at'])

    def __str__(self):
        return f"{self.invoice_number} - ${self.total} ({self.get_status_display()})"


class Payment(models.Model):
    METHOD_CASH = 'CASH'
    METHOD_CARD = 'CARD'
    METHOD_UPI = 'UPI'
    METHOD_BANK_TRANSFER = 'BANK_TRANSFER'

    METHOD_CHOICES = [
        (METHOD_CASH, 'Cash'),
        (METHOD_CARD, 'Credit / Debit Card'),
        (METHOD_UPI, 'UPI'),
        (METHOD_BANK_TRANSFER, 'Bank Transfer / NEFT'),
    ]

    STATUS_SUCCESS = 'SUCCESS'
    STATUS_PENDING = 'PENDING'
    STATUS_FAILED = 'FAILED'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_FAILED, 'Failed'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Payment amount (must be positive)"
    )
    method = models.CharField(max_length=30, choices=METHOD_CHOICES, default=METHOD_CARD)
    reference = models.CharField(max_length=100, blank=True, help_text="Transaction ID, cheque number, or gateway ref")
    paid_on = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-paid_on', '-id']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def clean(self):
        super().clean()
        if self.amount is not None:
            if self.amount <= Decimal('0.00'):
                raise ValidationError({'amount': 'Payment amount must be greater than zero.'})
            # Prevent payment exceeding balance due (for new payments or amount increases)
            if self.invoice_id:
                current_balance = self.invoice.balance_due
                # If editing existing payment, add back current payment amount to available balance
                if self.pk:
                    existing = Payment.objects.filter(pk=self.pk).first()
                    if existing and existing.status == self.STATUS_SUCCESS:
                        current_balance += existing.amount
                if self.status == self.STATUS_SUCCESS and self.amount > current_balance:
                    raise ValidationError({'amount': f"Payment amount (${self.amount}) exceeds balance due (${current_balance})."})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update invoice status automatically when payment is recorded
        self.invoice.update_payment_status()

    def __str__(self):
        return f"Payment #{self.id} (${self.amount} via {self.get_method_display()} for {self.invoice.invoice_number})"
