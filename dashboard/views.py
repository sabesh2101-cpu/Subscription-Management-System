import json
from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, ListView
from django.db.models import Sum, Count, Q
from django.utils import timezone

from accounts.models import User
from accounts.permissions import RoleRequiredMixin
from catalog.models import Product, SubscriptionPlan
from billing.models import Discount, Invoice, Payment
from subscriptions.models import Subscription
from .models import MSMEStatistic
from .services import get_dashboard_summary, get_staff_workbench_data


def render_admin_dashboard(request):
    """Renders Executive & System Admin Control Hub."""
    summary = get_dashboard_summary()
    msme_stats = MSMEStatistic.objects.all().order_by('-year', 'state')[:8]
    msme_sector_agg = MSMEStatistic.objects.values('sector').annotate(
        total_units=Sum('registered_units')
    ).order_by('-total_units')[:6]

    monthly_rev_labels = [m['month'] for m in summary['monthly_revenue']]
    monthly_rev_values = [m['amount'] for m in summary['monthly_revenue']]

    status_labels = [s['label'] for s in summary['status_breakdown']]
    status_counts = [s['count'] for s in summary['status_breakdown']]

    admin_metrics = {
        'total_admins': User.objects.filter(role=User.ROLE_ADMIN).count(),
        'total_staff': User.objects.filter(role=User.ROLE_STAFF).count(),
        'total_customers': User.objects.filter(role=User.ROLE_CUSTOMER).count(),
        'total_products': Product.objects.count(),
        'total_plans': SubscriptionPlan.objects.count(),
        'total_discounts': Discount.objects.count(),
    }

    context = {
        'is_admin_dashboard': True,
        'summary': summary,
        'admin_metrics': admin_metrics,
        'msme_stats': msme_stats,
        'msme_sectors': msme_sector_agg,
        'monthly_rev_labels_json': json.dumps(monthly_rev_labels),
        'monthly_rev_values_json': json.dumps(monthly_rev_values),
        'status_labels_json': json.dumps(status_labels),
        'status_counts_json': json.dumps(status_counts),
    }
    return render(request, 'dashboard/executive_dashboard.html', context)


def render_staff_dashboard(request):
    """Renders Staff Operations & Billing Workbench."""
    workbench = get_staff_workbench_data()
    context = {
        'is_staff_workbench': True,
        'workbench': workbench,
    }
    return render(request, 'dashboard/staff_dashboard.html', context)


def render_customer_dashboard(request):
    """Renders Customer Self-Service Portal."""
    user = request.user
    customer_subs = Subscription.objects.filter(customer=user).select_related('plan', 'plan__product')
    active_subs = customer_subs.filter(status=Subscription.STATUS_ACTIVE)
    customer_invoices = Invoice.objects.filter(subscription__customer=user).select_related('subscription', 'subscription__plan')
    unpaid_invoices = customer_invoices.filter(status__in=[Invoice.STATUS_SENT, Invoice.STATUS_OVERDUE])
    unpaid_total = sum((inv.balance_due for inv in unpaid_invoices), Decimal('0.00'))

    total_paid = Payment.objects.filter(
        invoice__subscription__customer=user,
        status=Payment.STATUS_SUCCESS
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    recent_invoices = customer_invoices.order_by('-issue_date')[:5]

    context = {
        'is_customer_dashboard': True,
        'total_subscriptions': customer_subs.count(),
        'active_subscriptions': active_subs.count(),
        'active_subs_list': active_subs[:4],
        'unpaid_count': unpaid_invoices.count(),
        'unpaid_total': unpaid_total,
        'total_paid': total_paid,
        'recent_invoices': recent_invoices,
    }
    return render(request, 'dashboard/customer_dashboard.html', context)


class DashboardIndexView(LoginRequiredMixin, View):
    """Central router: directs Admin, Staff, and Customer to their dedicated dashboards."""
    def get(self, request, *args, **kwargs):
        if request.user.is_admin_role:
            return render_admin_dashboard(request)
        elif request.user.is_staff_role:
            return render_staff_dashboard(request)
        else:
            return render_customer_dashboard(request)


class AdminHubView(RoleRequiredMixin, View):
    """Dedicated Admin Hub view (accessible by Admin)."""
    allowed_roles = [User.ROLE_ADMIN]

    def get(self, request, *args, **kwargs):
        return render_admin_dashboard(request)


class StaffWorkbenchView(RoleRequiredMixin, View):
    """Dedicated Staff Operations Workbench (accessible by Staff & Admin)."""
    allowed_roles = [User.ROLE_ADMIN, User.ROLE_STAFF]

    def get(self, request, *args, **kwargs):
        return render_staff_dashboard(request)


class MSMEStatisticsView(LoginRequiredMixin, ListView):
    model = MSMEStatistic
    template_name = 'dashboard/msme_statistics.html'
    context_object_name = 'statistics'
    paginate_by = 15

    def get_queryset(self):
        qs = MSMEStatistic.objects.all().order_by('-year', 'state', 'sector')
        state = self.request.GET.get('state')
        if state:
            qs = qs.filter(state__icontains=state)
        sector = self.request.GET.get('sector')
        if sector:
            qs = qs.filter(sector__icontains=sector)
        year = self.request.GET.get('year')
        if year:
            qs = qs.filter(year=year)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['state_filter'] = self.request.GET.get('state', '')
        context['sector_filter'] = self.request.GET.get('sector', '')
        context['year_filter'] = self.request.GET.get('year', '')

        top_sectors = MSMEStatistic.objects.values('sector').annotate(
            total_units=Sum('registered_units')
        ).order_by('-total_units')[:7]

        context['chart_sectors_json'] = json.dumps([s['sector'] for s in top_sectors])
        context['chart_units_json'] = json.dumps([s['total_units'] for s in top_sectors])
        return context
