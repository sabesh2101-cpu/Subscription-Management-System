import json
from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, ListView
from django.db.models import Sum, Count, Q
from django.utils import timezone
from .models import MSMEStatistic
from .services import get_dashboard_summary
from subscriptions.models import Subscription
from billing.models import Invoice, Payment


class DashboardIndexView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user

        if user.is_staff_role:
            # Executive & Staff Dashboard
            summary = get_dashboard_summary()
            msme_stats = MSMEStatistic.objects.all().order_by('-year', 'state')[:10]
            msme_sector_agg = MSMEStatistic.objects.values('sector').annotate(
                total_units=Sum('registered_units')
            ).order_by('-total_units')[:6]

            # Prepare chart JSON payloads
            monthly_rev_labels = [m['month'] for m in summary['monthly_revenue']]
            monthly_rev_values = [m['amount'] for m in summary['monthly_revenue']]

            status_labels = [s['label'] for s in summary['status_breakdown']]
            status_counts = [s['count'] for s in summary['status_breakdown']]

            context = {
                'is_staff_dashboard': True,
                'summary': summary,
                'msme_stats': msme_stats,
                'msme_sectors': msme_sector_agg,
                'monthly_rev_labels_json': json.dumps(monthly_rev_labels),
                'monthly_rev_values_json': json.dumps(monthly_rev_values),
                'status_labels_json': json.dumps(status_labels),
                'status_counts_json': json.dumps(status_counts),
            }
            return render(request, 'dashboard/executive_dashboard.html', context)

        else:
            # Customer Portal Dashboard
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
                'is_staff_dashboard': False,
                'total_subscriptions': customer_subs.count(),
                'active_subscriptions': active_subs.count(),
                'active_subs_list': active_subs[:4],
                'unpaid_count': unpaid_invoices.count(),
                'unpaid_total': unpaid_total,
                'total_paid': total_paid,
                'recent_invoices': recent_invoices,
            }
            return render(request, 'dashboard/customer_dashboard.html', context)


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

        # Aggregation for top sectors chart
        top_sectors = MSMEStatistic.objects.values('sector').annotate(
            total_units=Sum('registered_units')
        ).order_by('-total_units')[:7]

        context['chart_sectors_json'] = json.dumps([s['sector'] for s in top_sectors])
        context['chart_units_json'] = json.dumps([s['total_units'] for s in top_sectors])
        return context
