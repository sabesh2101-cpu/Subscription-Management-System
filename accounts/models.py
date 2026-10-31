from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = 'ADMIN'
    ROLE_STAFF = 'STAFF'
    ROLE_CUSTOMER = 'CUSTOMER'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_STAFF, 'Staff'),
        (ROLE_CUSTOMER, 'Customer'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    phone = models.CharField(max_length=25, blank=True, null=True)
    company_name = models.CharField(max_length=150, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['username']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    @property
    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def is_staff_role(self):
        return self.role in [self.ROLE_ADMIN, self.ROLE_STAFF] or self.is_staff or self.is_superuser

    @property
    def is_customer_role(self):
        return self.role == self.ROLE_CUSTOMER and not self.is_superuser

    def save(self, *args, **kwargs):
        if self.role == self.ROLE_ADMIN:
            self.is_staff = True
        elif self.role == self.ROLE_STAFF:
            self.is_staff = True
        elif self.role == self.ROLE_CUSTOMER and not self.is_superuser:
            self.is_staff = False
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.get_full_name() or self.username
        if self.company_name:
            return f"{name} ({self.company_name}) [{self.get_role_display()}]"
        return f"{name} [{self.get_role_display()}]"
