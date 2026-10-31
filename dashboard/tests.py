from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from catalog.models import Product, SubscriptionPlan
from subscriptions.models import Subscription
from billing.models import Discount
from dashboard.services import calculate_mrr


class MRRCalculationTestCase(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username='mrr_customer',
            password='password123',
            role=User.ROLE_CUSTOMER
        )
        self.product = Product.objects.create(
            name='Analytics Suite',
            sku='ANALYTICS-X',
            price=Decimal('100.00')
        )

        # Monthly plan: $50/mo => MRR contribution $50
        self.plan_monthly = SubscriptionPlan.objects.create(
            product=self.product,
            name='Monthly Plan',
            billing_cycle=SubscriptionPlan.CYCLE_MONTHLY,
            price=Decimal('50.00')
        )

        # Quarterly plan: $120/quarter => $120 / 3 = $40/mo MRR contribution
        self.plan_quarterly = SubscriptionPlan.objects.create(
            product=self.product,
            name='Quarterly Plan',
            billing_cycle=SubscriptionPlan.CYCLE_QUARTERLY,
            price=Decimal('120.00')
        )

        # Yearly plan: $1200/year => $1200 / 12 = $100/mo MRR contribution
        self.plan_yearly = SubscriptionPlan.objects.create(
            product=self.product,
            name='Yearly Plan',
            billing_cycle=SubscriptionPlan.CYCLE_YEARLY,
            price=Decimal('1200.00')
        )

    def test_mrr_normalized_across_cycles(self):
        # 1 active monthly: $50
        Subscription.objects.create(
            customer=self.customer,
            plan=self.plan_monthly,
            status=Subscription.STATUS_ACTIVE
        )

        # 1 active quarterly: $120 / 3 = $40
        Subscription.objects.create(
            customer=self.customer,
            plan=self.plan_quarterly,
            status=Subscription.STATUS_ACTIVE
        )

        # 1 active yearly: $1200 / 12 = $100
        Subscription.objects.create(
            customer=self.customer,
            plan=self.plan_yearly,
            status=Subscription.STATUS_ACTIVE
        )

        # Total expected MRR = 50 + 40 + 100 = 190.00
        total_mrr = calculate_mrr()
        self.assertEqual(total_mrr, Decimal('190.00'))

    def test_mrr_ignores_inactive_subscriptions(self):
        # Active monthly: $50
        Subscription.objects.create(
            customer=self.customer,
            plan=self.plan_monthly,
            status=Subscription.STATUS_ACTIVE
        )

        # Paused monthly: should be ignored
        Subscription.objects.create(
            customer=self.customer,
            plan=self.plan_monthly,
            status=Subscription.STATUS_PAUSED
        )

        # Cancelled yearly: should be ignored
        Subscription.objects.create(
            customer=self.customer,
            plan=self.plan_yearly,
            status=Subscription.STATUS_CANCELLED
        )

        # Draft quarterly: should be ignored
        Subscription.objects.create(
            customer=self.customer,
            plan=self.plan_quarterly,
            status=Subscription.STATUS_DRAFT
        )

        total_mrr = calculate_mrr()
        self.assertEqual(total_mrr, Decimal('50.00'))

    def test_mrr_with_discount(self):
        today = timezone.now().date()
        discount = Discount.objects.create(
            code='MRR10',
            type=Discount.TYPE_PERCENT,
            value=Decimal('10.00'), # 10% off
            valid_from=today - timedelta(days=5),
            valid_to=today + timedelta(days=30),
            is_active=True
        )

        # Monthly $50 with 10% discount ($5 off) => $45/mo
        Subscription.objects.create(
            customer=self.customer,
            plan=self.plan_monthly,
            status=Subscription.STATUS_ACTIVE,
            discount=discount
        )

        total_mrr = calculate_mrr()
        self.assertEqual(total_mrr, Decimal('45.00'))
