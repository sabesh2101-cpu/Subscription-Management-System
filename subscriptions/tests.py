import datetime
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from accounts.models import User
from catalog.models import Product, SubscriptionPlan
from subscriptions.models import Subscription, compute_next_billing_date
from billing.models import Discount, Invoice


class SubscriptionModelTestCase(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username='sub_tester',
            password='password123',
            role=User.ROLE_CUSTOMER
        )
        self.product = Product.objects.create(
            name='Test Product',
            sku='TEST-001',
            price=Decimal('50.00')
        )
        self.plan = SubscriptionPlan.objects.create(
            product=self.product,
            name='Pro Monthly',
            billing_cycle=SubscriptionPlan.CYCLE_MONTHLY,
            price=Decimal('50.00')
        )
        self.discount = Discount.objects.create(
            code='DISC20',
            type=Discount.TYPE_PERCENT,
            value=Decimal('20.00'),
            valid_from=timezone.localdate() - datetime.timedelta(days=1),
            valid_to=timezone.localdate() + datetime.timedelta(days=30),
            is_active=True
        )

    def test_subscription_clean_with_default_date_and_discount(self):
        # When Subscription is instantiated without start_date, start_date is set to default
        sub = Subscription(customer=self.customer, plan=self.plan, discount=self.discount)
        # Calling clean() should NOT raise TypeError: '<' not supported between instances of 'datetime.datetime' and 'datetime.date'
        sub.clean()
        sub.save()
        self.assertEqual(sub.status, Subscription.STATUS_ACTIVE)
        self.assertEqual(sub.current_cycle_cost, Decimal('40.00'))

    def test_invoice_clean_with_default_date(self):
        sub = Subscription.objects.create(customer=self.customer, plan=self.plan)
        inv = Invoice(subscription=sub, due_date=timezone.localdate() + datetime.timedelta(days=15), subtotal=Decimal('50.00'), total=Decimal('50.00'))
        # Calling clean() should NOT raise TypeError
        inv.clean()
        inv.save()
        self.assertTrue(inv.invoice_number.startswith('INV-'))

    def test_discount_clean_with_default_date(self):
        disc = Discount(code='PROMO1', value=Decimal('10.00'), valid_to=timezone.localdate() + datetime.timedelta(days=10))
        # Calling clean() should NOT raise TypeError
        disc.clean()
        disc.save()
        self.assertEqual(disc.code, 'PROMO1')

    def test_billing_cycle_computation_eom(self):
        # Jan 31 -> Feb 28
        jan31 = datetime.date(2026, 1, 31)
        next_date = compute_next_billing_date(jan31, SubscriptionPlan.CYCLE_MONTHLY)
        self.assertEqual(next_date, datetime.date(2026, 2, 28))

    def test_subscription_lifecycle(self):
        sub = Subscription.objects.create(customer=self.customer, plan=self.plan)
        self.assertEqual(sub.status, Subscription.STATUS_ACTIVE)

        sub.pause()
        self.assertEqual(sub.status, Subscription.STATUS_PAUSED)

        sub.activate()
        self.assertEqual(sub.status, Subscription.STATUS_ACTIVE)

        sub.cancel()
        self.assertEqual(sub.status, Subscription.STATUS_CANCELLED)
        self.assertIsNotNone(sub.end_date)
