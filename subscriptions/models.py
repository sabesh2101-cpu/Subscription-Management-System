import calendar
import datetime
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from catalog.models import SubscriptionPlan


def to_date(val):
    if val is None:
        return None
    if isinstance(val, datetime.datetime):
        return val.date()
    return val


def compute_next_billing_date(from_date, billing_cycle):
    """Computes next billing date based on cycle with end-of-month clamping."""
    from_date = to_date(from_date) or timezone.localdate()
    year = from_date.year
    month = from_date.month
    day = from_date.day

    if billing_cycle == SubscriptionPlan.CYCLE_MONTHLY:
        month += 1
        if month > 12:
            month = 1
            year += 1
    elif billing_cycle == SubscriptionPlan.CYCLE_QUARTERLY:
        month += 3
        if month > 12:
            month -= 12
            year += 1
    elif billing_cycle == SubscriptionPlan.CYCLE_YEARLY:
        year += 1

    max_day = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, min(day, max_day))


class Subscription(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_PAUSED = 'PAUSED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_EXPIRED = 'EXPIRED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_PAUSED, 'Paused'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_EXPIRED, 'Expired'),
    ]

    customer = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        limit_choices_to={'role': 'CUSTOMER'}
    )
    plan = models.ForeignKey(
        'catalog.SubscriptionPlan',
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    start_date = models.DateField(default=timezone.localdate)
    next_billing_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    discount = models.ForeignKey(
        'billing.Discount',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subscriptions'
    )
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def clean(self):
        super().clean()
        start_date = to_date(self.start_date)
        end_date = to_date(self.end_date)
        if start_date and end_date and end_date < start_date:
            raise ValidationError({'end_date': 'End date cannot be earlier than start date.'})
        if self.discount:
            is_valid, reason = self.discount.is_currently_valid(start_date)
            if not is_valid:
                raise ValidationError({'discount': f"Selected discount cannot be applied: {reason}"})

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.localdate()
        else:
            self.start_date = to_date(self.start_date)
        if self.end_date:
            self.end_date = to_date(self.end_date)
        if self.next_billing_date:
            self.next_billing_date = to_date(self.next_billing_date)
        elif self.plan:
            self.next_billing_date = compute_next_billing_date(self.start_date, self.plan.billing_cycle)
        super().save(*args, **kwargs)

    @property
    def current_cycle_cost(self):
        """Calculates final recurring price after applying any attached discount."""
        base_price = self.plan.price
        if self.discount and self.discount.is_active:
            discount_val = self.discount.calculate_discount_amount(base_price)
            return max(Decimal('0.00'), base_price - discount_val)
        return base_price

    @property
    def mrr_contribution(self):
        """Calculates this subscription's contribution to Monthly Recurring Revenue."""
        if self.status != self.STATUS_ACTIVE:
            return Decimal('0.00')
        cost = self.current_cycle_cost
        if self.plan.billing_cycle == SubscriptionPlan.CYCLE_YEARLY:
            return (cost / Decimal('12.0')).quantize(Decimal('0.01'))
        elif self.plan.billing_cycle == SubscriptionPlan.CYCLE_QUARTERLY:
            return (cost / Decimal('3.0')).quantize(Decimal('0.01'))
        return cost.quantize(Decimal('0.01'))

    def advance_billing_cycle(self):
        """Advances next_billing_date after invoice/payment cycle."""
        base_date = self.next_billing_date or self.start_date
        self.next_billing_date = compute_next_billing_date(base_date, self.plan.billing_cycle)
        self.save(update_fields=['next_billing_date', 'updated_at'])

    def activate(self):
        self.status = self.STATUS_ACTIVE
        if not self.next_billing_date:
            self.next_billing_date = compute_next_billing_date(timezone.localdate(), self.plan.billing_cycle)
        self.save(update_fields=['status', 'next_billing_date', 'updated_at'])

    def pause(self):
        self.status = self.STATUS_PAUSED
        self.save(update_fields=['status', 'updated_at'])

    def cancel(self):
        self.status = self.STATUS_CANCELLED
        self.end_date = timezone.localdate()
        self.save(update_fields=['status', 'end_date', 'updated_at'])

    def __str__(self):
        return f"Sub #{self.id}: {self.customer.username} - {self.plan.name} ({self.get_status_display()})"
