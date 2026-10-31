from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from accounts.models import User
from catalog.models import Product, SubscriptionPlan
from subscriptions.models import Subscription
from billing.models import Discount, Invoice, Payment
from billing.services import generate_invoice_for_subscription, record_payment


class BillingTestCase(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username='billing_customer',
            password='password123',
            role=User.ROLE_CUSTOMER
        )
        self.product = Product.objects.create(
            name='Cloud SaaS',
            sku='SAAS-01',
            price=Decimal('100.00')
        )
        self.plan = SubscriptionPlan.objects.create(
            product=self.product,
            name='Monthly Standard',
            billing_cycle=SubscriptionPlan.CYCLE_MONTHLY,
            price=Decimal('100.00')
        )
        self.subscription = Subscription.objects.create(
            customer=self.customer,
            plan=self.plan,
            status=Subscription.STATUS_ACTIVE
        )

    def test_invoice_numbering_auto_generation(self):
        inv1 = Invoice.objects.create(
            subscription=self.subscription,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=15),
            subtotal=Decimal('100.00'),
            total=Decimal('100.00')
        )
        inv2 = Invoice.objects.create(
            subscription=self.subscription,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=15),
            subtotal=Decimal('100.00'),
            total=Decimal('100.00')
        )

        year = timezone.now().year
        self.assertTrue(inv1.invoice_number.startswith(f"INV-{year}-"))
        self.assertTrue(inv2.invoice_number.startswith(f"INV-{year}-"))

        seq1 = int(inv1.invoice_number.split('-')[-1])
        seq2 = int(inv2.invoice_number.split('-')[-1])
        self.assertEqual(seq2, seq1 + 1)

    def test_percentage_discount_calculation(self):
        today = timezone.now().date()
        discount = Discount.objects.create(
            code='SAVE20',
            type=Discount.TYPE_PERCENT,
            value=Decimal('20.00'),
            valid_from=today - timedelta(days=10),
            valid_to=today + timedelta(days=10),
            is_active=True
        )

        subtotal = Decimal('100.00')
        discount_amount = discount.calculate_discount_amount(subtotal)
        self.assertEqual(discount_amount, Decimal('20.00'))

        # Discount cannot exceed subtotal
        huge_discount = Discount.objects.create(
            code='SAVE100',
            type=Discount.TYPE_PERCENT,
            value=Decimal('100.00'),
            valid_from=today,
            valid_to=today + timedelta(days=5),
            is_active=True
        )
        self.assertEqual(huge_discount.calculate_discount_amount(subtotal), Decimal('100.00'))

    def test_fixed_discount_calculation(self):
        today = timezone.now().date()
        discount = Discount.objects.create(
            code='FLAT30',
            type=Discount.TYPE_FIXED,
            value=Decimal('30.00'),
            valid_from=today - timedelta(days=5),
            valid_to=today + timedelta(days=5),
            is_active=True
        )

        subtotal = Decimal('100.00')
        self.assertEqual(discount.calculate_discount_amount(subtotal), Decimal('30.00'))

        # Flat discount capped at subtotal
        small_subtotal = Decimal('20.00')
        self.assertEqual(discount.calculate_discount_amount(small_subtotal), Decimal('20.00'))

    def test_discount_validity_dates_and_limit(self):
        today = timezone.now().date()
        expired = Discount.objects.create(
            code='OLDCODE',
            type=Discount.TYPE_PERCENT,
            value=Decimal('10.00'),
            valid_from=today - timedelta(days=30),
            valid_to=today - timedelta(days=1),
            is_active=True
        )
        is_valid, msg = expired.is_currently_valid()
        self.assertFalse(is_valid)

        capped = Discount.objects.create(
            code='LIMITED',
            type=Discount.TYPE_PERCENT,
            value=Decimal('10.00'),
            valid_from=today,
            valid_to=today + timedelta(days=10),
            usage_limit=1,
            times_used=1,
            is_active=True
        )
        is_valid, msg = capped.is_currently_valid()
        self.assertFalse(is_valid)

    def test_invoice_generation_service(self):
        today = timezone.now().date()
        discount = Discount.objects.create(
            code='PROMO15',
            type=Discount.TYPE_PERCENT,
            value=Decimal('15.00'),
            valid_from=today - timedelta(days=1),
            valid_to=today + timedelta(days=30),
            is_active=True
        )
        self.subscription.discount = discount
        self.subscription.save()

        invoice = generate_invoice_for_subscription(self.subscription)
        self.assertEqual(invoice.subtotal, Decimal('100.00'))
        self.assertEqual(invoice.discount_amount, Decimal('15.00'))
        self.assertEqual(invoice.total, Decimal('85.00'))
        self.assertEqual(invoice.status, Invoice.STATUS_SENT)

    def test_payment_marks_invoice_paid(self):
        invoice = generate_invoice_for_subscription(self.subscription)
        self.assertEqual(invoice.status, Invoice.STATUS_SENT)
        self.assertEqual(invoice.balance_due, Decimal('100.00'))

        # Record full payment
        payment = record_payment(
            invoice=invoice,
            amount=Decimal('100.00'),
            method=Payment.METHOD_CARD,
            reference='TXN-TEST-100'
        )

        invoice.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_SUCCESS)
        self.assertEqual(invoice.balance_due, Decimal('0.00'))
        self.assertEqual(invoice.status, Invoice.STATUS_PAID)

    def test_partial_payment_keeps_invoice_unpaid(self):
        invoice = generate_invoice_for_subscription(self.subscription)

        # Record partial payment of $40
        record_payment(
            invoice=invoice,
            amount=Decimal('40.00'),
            method=Payment.METHOD_UPI,
            reference='UPI-PARTIAL'
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.total_paid, Decimal('40.00'))
        self.assertEqual(invoice.balance_due, Decimal('60.00'))
        self.assertEqual(invoice.status, Invoice.STATUS_SENT)

        # Settle the remaining balance
        record_payment(
            invoice=invoice,
            amount=Decimal('60.00'),
            method=Payment.METHOD_BANK_TRANSFER,
            reference='BANK-FINAL'
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.balance_due, Decimal('0.00'))
        self.assertEqual(invoice.status, Invoice.STATUS_PAID)

    def test_payment_cannot_exceed_balance_due(self):
        invoice = generate_invoice_for_subscription(self.subscription)
        with self.assertRaises(ValidationError):
            record_payment(
                invoice=invoice,
                amount=Decimal('150.00'), # Exceeds $100
                method=Payment.METHOD_CASH
            )
