import datetime
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Invoice, Payment, to_date


def generate_invoice_for_subscription(subscription, issue_date=None, due_date=None, tax_rate=Decimal('0.00'), notes=''):
    """
    Generates a new Invoice for a given subscription using plan pricing,
    applying any valid discount and optional tax.
    """
    issue_date = to_date(issue_date) or timezone.localdate()
    if not due_date:
        due_date = issue_date + timedelta(days=15)
    else:
        due_date = to_date(due_date)

    subtotal = subscription.plan.price
    discount_amount = Decimal('0.00')

    # Apply attached discount if valid
    if subscription.discount:
        is_valid, _ = subscription.discount.is_currently_valid(issue_date)
        if is_valid:
            discount_amount = subscription.discount.calculate_discount_amount(subtotal)
            # Increment usage count atomically
            subscription.discount.times_used += 1
            subscription.discount.save(update_fields=['times_used'])

    tax_rate = Decimal(str(tax_rate))
    taxable_amount = max(Decimal('0.00'), subtotal - discount_amount)
    tax_amount = (taxable_amount * (tax_rate / Decimal('100.0'))).quantize(Decimal('0.01'))
    total = taxable_amount + tax_amount

    invoice = Invoice.objects.create(
        subscription=subscription,
        issue_date=issue_date,
        due_date=due_date,
        subtotal=subtotal,
        discount_amount=discount_amount,
        tax_amount=tax_amount,
        total=total,
        status=Invoice.STATUS_SENT,
        notes=notes or f"Generated recurring invoice for {subscription.plan.name}"
    )
    return invoice


@transaction.atomic
def record_payment(invoice, amount, method, reference='', paid_on=None, notes=''):
    """
    Records a payment for an invoice and reconciles invoice status (marks PAID if fully paid).
    """
    amount = Decimal(str(amount))
    if amount <= Decimal('0.00'):
        raise ValidationError("Payment amount must be greater than zero.")

    balance = invoice.balance_due
    if amount > balance:
        raise ValidationError(f"Payment amount (${amount}) exceeds invoice balance due (${balance}).")

    if not paid_on:
        paid_on = timezone.now()

    payment = Payment.objects.create(
        invoice=invoice,
        amount=amount,
        method=method,
        reference=reference,
        paid_on=paid_on,
        status=Payment.STATUS_SUCCESS,
        notes=notes
    )

    # Re-evaluate invoice status
    invoice.refresh_from_db()
    invoice.update_payment_status()

    return payment
