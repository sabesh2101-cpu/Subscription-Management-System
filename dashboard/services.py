import calendar
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
    today = timezone.now().date()

    for inv in unpaid_invoices:
        bal = inv.balance_due
        if bal > Decimal('0.00'):
            outstanding_amount += bal
            if inv.status == Invoice.STATUS_OVERDUE or inv.due_date < today:
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
