from django.contrib import admin
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'plan', 'start_date', 'next_billing_date', 'status', 'discount']
    list_filter = ['status', 'plan__billing_cycle', 'start_date']
    search_fields = ['customer__username', 'customer__email', 'plan__name']
