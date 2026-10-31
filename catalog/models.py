from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    sku = models.CharField(max_length=50, unique=True, help_text="Unique Stock Keeping Unit")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Base/standalone price (must be non-negative)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def clean(self):
        super().clean()
        if self.price is not None and self.price < Decimal('0.00'):
            raise ValidationError({'price': 'Product price cannot be negative.'})

    def __str__(self):
        return f"{self.name} ({self.sku}) - ${self.price}"


class SubscriptionPlan(models.Model):
    CYCLE_MONTHLY = 'MONTHLY'
    CYCLE_QUARTERLY = 'QUARTERLY'
    CYCLE_YEARLY = 'YEARLY'

    CYCLE_CHOICES = [
        (CYCLE_MONTHLY, 'Monthly'),
        (CYCLE_QUARTERLY, 'Quarterly (3 Months)'),
        (CYCLE_YEARLY, 'Yearly (12 Months)'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='plans')
    name = models.CharField(max_length=150)
    billing_cycle = models.CharField(max_length=20, choices=CYCLE_CHOICES, default=CYCLE_MONTHLY)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Recurring price per cycle"
    )
    trial_days = models.PositiveIntegerField(default=0, help_text="Trial duration in days")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['product__name', 'price']
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'

    def clean(self):
        super().clean()
        if self.price is not None and self.price < Decimal('0.00'):
            raise ValidationError({'price': 'Plan price cannot be negative.'})

    @property
    def normalized_monthly_price(self):
        """Calculates normalized monthly revenue equivalent for MRR."""
        if self.billing_cycle == self.CYCLE_YEARLY:
            return (self.price / Decimal('12.0')).quantize(Decimal('0.01'))
        elif self.billing_cycle == self.CYCLE_QUARTERLY:
            return (self.price / Decimal('3.0')).quantize(Decimal('0.01'))
        return self.price

    def __str__(self):
        return f"{self.product.name} - {self.name} (${self.price} / {self.get_billing_cycle_display()})"
