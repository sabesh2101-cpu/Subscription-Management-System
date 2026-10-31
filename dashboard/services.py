import calendar
import datetime
from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Count, Q
from django.utils import timezone
from subscriptions.models import Subscription
from billing.models import Invoice, Payment
from catalog.models import SubscriptionPlan


def calculate_mrr():
    """
    Calculates total Monthly Recurring Revenue (MRR) normalized across billing cycles:
    - Monthly: full price (post-discount)
    - Quarterly: price / 3 (post-discount)
    - Yearly: price / 12 (post-discount)
    Only ACTIVE subscriptions are counted.
    """
    active_subscriptions = Subscription.objects.filter(
        status=Subscription.STATUS_ACTIVE
    ).select_related('plan', 'discount')

    total_mrr = Decimal('0.00')
    for sub in active_subscriptions:
        total_mrr += sub.mrr_contribution

    return total_mrr.quantize(Decimal('0.01'))


def get_revenue_last_12_months():
    """
    Returns monthly revenue for the past 12 months including current month.
    """
    today = timezone.now().date()
    months_data = []

    # Build sequence of the last 12 months (oldest to current)
    for i in range(11, -1, -1):
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1

        first_day = date(year, month, 1)
        _, last_day_num = calendar.monthrange(year, month)
        last_day = date(year, month, last_day_num)

        rev = Payment.objects.filter(
            status=Payment.STATUS_SUCCESS,
            paid_on__date__gte=first_day,
            paid_on__date__lte=last_day
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        month_label = first_day.strftime('%b %Y')
        months_data.append({
            'month': month_label,
            'amount': float(rev)
        })

    return months_data


def get_subscription_status_breakdown():
    """
    Returns count and labels for subscription status chart.
    """
    counts = Subscription.objects.values('status').annotate(count=Count('id'))
    status_map = {item['status']: item['count'] for item in counts}

    results = []
    for code, label in Subscription.STATUS_CHOICES:
        results.append({
            'code': code,
            'label': label,
            'count': status_map.get(code, 0)
        })
    return results


def get_dashboard_summary():
    """
    Aggregates all key KPIs for the executive dashboard.
    """
    mrr = calculate_mrr()
    arr = (mrr * Decimal('12.0')).quantize(Decimal('0.01'))

    total_revenue = Payment.objects.filter(
        status=Payment.STATUS_SUCCESS
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    active_subscriptions_count = Subscription.objects.filter(
        status=Subscription.STATUS_ACTIVE
    ).count()

    total_subscriptions_count = Subscription.objects.count()

    # Invoices outstanding & overdue
    unpaid_invoices = Invoice.objects.filter(
        status__in=[Invoice.STATUS_SENT, Invoice.STATUS_OVERDUE, Invoice.STATUS_DRAFT]
    ).prefetch_related('payments')

    outstanding_amount = Decimal('0.00')
    overdue_amount = Decimal('0.00')
    today = timezone.localdate()

    for inv in unpaid_invoices:
        bal = inv.balance_due
        if bal > Decimal('0.00'):
            outstanding_amount += bal
            due = inv.due_date.date() if isinstance(inv.due_date, datetime.datetime) else inv.due_date
            if inv.status == Invoice.STATUS_OVERDUE or (due and due < today):
                overdue_amount += bal

    recent_payments = Payment.objects.filter(
        status=Payment.STATUS_SUCCESS
    ).select_related('invoice', 'invoice__subscription', 'invoice__subscription__customer')[:6]

    return {
        'mrr': mrr,
        'arr': arr,
        'total_revenue': total_revenue,
        'active_subscriptions_count': active_subscriptions_count,
        'total_subscriptions_count': total_subscriptions_count,
        'outstanding_amount': outstanding_amount.quantize(Decimal('0.01')),
        'overdue_amount': overdue_amount.quantize(Decimal('0.01')),
        'recent_payments': recent_payments,
        'status_breakdown': get_subscription_status_breakdown(),
        'monthly_revenue': get_revenue_last_12_months(),
    }


def get_staff_workbench_data():
    """
    Aggregates operational task queues for Staff:
    - Invoices requiring action/follow-up
    - Subscriptions renewing soon
    - Today's and monthly collections
    - Recent payment remittances
    """
    today = timezone.localdate()
    in_14_days = today + timedelta(days=14)

    # 1. Unpaid & Overdue Invoices
    unpaid_qs = Invoice.objects.filter(
        status__in=[Invoice.STATUS_SENT, Invoice.STATUS_OVERDUE]
    ).select_related('subscription', 'subscription__customer', 'subscription__plan').prefetch_related('payments').order_by('due_date')

    unpaid_list = list(unpaid_qs)
    overdue_list = [inv for inv in unpaid_list if inv.due_date < today or inv.status == Invoice.STATUS_OVERDUE]

    total_unpaid_amount = sum((inv.balance_due for inv in unpaid_list), Decimal('0.00')).quantize(Decimal('0.01'))
    total_overdue_amount = sum((inv.balance_due for inv in overdue_list), Decimal('0.00')).quantize(Decimal('0.01'))

    # 2. Upcoming billing subscriptions (due within 14 days)
    upcoming_subs = Subscription.objects.filter(
        status=Subscription.STATUS_ACTIVE,
        next_billing_date__lte=in_14_days
    ).select_related('customer', 'plan', 'plan__product').order_by('next_billing_date')

    # 3. Monthly and daily collections
    first_of_month = date(today.year, today.month, 1)
    month_collections = Payment.objects.filter(
        status=Payment.STATUS_SUCCESS,
        paid_on__date__gte=first_of_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    today_collections = Payment.objects.filter(
        status=Payment.STATUS_SUCCESS,
        paid_on__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    recent_payments = Payment.objects.filter(
        status=Payment.STATUS_SUCCESS
    ).select_related('invoice', 'invoice__subscription', 'invoice__subscription__customer').order_by('-paid_on')[:8]

    return {
        'today': today,
        'unpaid_invoices': unpaid_list[:12],
        'unpaid_count': len(unpaid_list),
        'overdue_count': len(overdue_list),
        'total_unpaid_amount': total_unpaid_amount,
        'total_overdue_amount': total_overdue_amount,
        'upcoming_billing_subs': upcoming_subs[:12],
        'upcoming_billing_count': upcoming_subs.count(),
        'month_collections': month_collections.quantize(Decimal('0.01')),
        'today_collections': today_collections.quantize(Decimal('0.01')),
        'recent_payments': recent_payments,
    }

