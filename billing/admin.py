from django.contrib import admin
from .models import Discount, Invoice, Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['paid_on']


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['code', 'type', 'value', 'valid_from', 'valid_to', 'usage_limit', 'times_used', 'is_active']
    list_filter = ['type', 'is_active', 'valid_from', 'valid_to']
    search_fields = ['code']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'subscription', 'issue_date', 'due_date', 'total', 'status']
    list_filter = ['status', 'issue_date', 'due_date']
    search_fields = ['invoice_number', 'subscription__customer__username', 'subscription__customer__company_name']
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'invoice', 'amount', 'method', 'reference', 'status', 'paid_on']
    list_filter = ['method', 'status', 'paid_on']
    search_fields = ['invoice__invoice_number', 'reference']
