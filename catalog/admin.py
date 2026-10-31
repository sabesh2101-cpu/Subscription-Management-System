from django.contrib import admin
from .models import Product, SubscriptionPlan


class SubscriptionPlanInline(admin.TabularInline):
    model = SubscriptionPlan
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'price', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'sku', 'description']
    inlines = [SubscriptionPlanInline]


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'billing_cycle', 'price', 'trial_days', 'is_active']
    list_filter = ['billing_cycle', 'is_active', 'product']
    search_fields = ['name', 'product__name']
