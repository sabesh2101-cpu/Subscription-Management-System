from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from catalog.models import Product


class RolePermissionsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin_test',
            password='password123',
            role=User.ROLE_ADMIN
        )
        self.staff = User.objects.create_user(
            username='staff_test',
            password='password123',
            role=User.ROLE_STAFF,
            is_staff=True
        )
        self.customer = User.objects.create_user(
            username='customer_test',
            password='password123',
            role=User.ROLE_CUSTOMER
        )
        self.product = Product.objects.create(
            name='Test Product',
            sku='TEST-PROD-01',
            price='50.00'
        )

    def test_admin_access_user_management(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_access_user_management(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_access_user_management(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_product_create(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('catalog:product_create'))
        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_create_product(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('catalog:product_create'))
        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_create_product(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse('catalog:product_create'))
        self.assertEqual(response.status_code, 403)

    def test_customer_can_browse_products(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse('catalog:product_list'))
        self.assertEqual(response.status_code, 200)
