from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'company_name', 'phone', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'company_name']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Roles & Profile', {
            'fields': ('role', 'company_name', 'phone', 'address')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Roles & Profile', {
            'fields': ('role', 'company_name', 'phone', 'address')
        }),
    )
