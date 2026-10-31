from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.db.models import Q
from accounts.models import User
from accounts.permissions import RoleRequiredMixin
from .models import Subscription
from .forms import SubscriptionForm
from billing.services import generate_invoice_for_subscription


class SubscriptionListView(LoginRequiredMixin, ListView):
    model = Subscription
    template_name = 'subscriptions/subscription_list.html'
    context_object_name = 'subscriptions'
    paginate_by = 12

    def get_queryset(self):
        qs = Subscription.objects.select_related(
            'customer', 'plan', 'plan__product', 'discount'
        )
        if self.request.user.is_customer_role:
            qs = qs.filter(customer=self.request.user)

        status_filter = self.request.GET.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        customer_filter = self.request.GET.get('customer')
        if customer_filter and self.request.user.is_staff_role:
            qs = qs.filter(customer_id=customer_filter)

        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(customer__username__icontains=q) |
                Q(customer__company_name__icontains=q) |
                Q(plan__name__icontains=q) |
                Q(plan__product__name__icontains=q)
            )

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['customer_filter'] = self.request.GET.get('customer', '')
        context['search_query'] = self.request.GET.get('q', '')
        if self.request.user.is_staff_role:
            context['all_customers'] = User.objects.filter(role=User.ROLE_CUSTOMER).order_by('username')
        return context


class SubscriptionDetailView(LoginRequiredMixin, DetailView):
    model = Subscription
    template_name = 'subscriptions/subscription_detail.html'
    context_object_name = 'subscription'

    def get_queryset(self):
        qs = Subscription.objects.select_related(
            'customer', 'plan', 'plan__product', 'discount'
        ).prefetch_related('invoices', 'invoices__payments')

        if self.request.user.is_customer_role:
            qs = qs.filter(customer=self.request.user)
        return qs


class SubscriptionCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [User.ROLE_ADMIN, User.ROLE_STAFF]
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'subscriptions/subscription_form.html'

    def get_success_url(self):
        return reverse('subscriptions:subscription_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Subscription created successfully.")
        return super().form_valid(form)


class SubscriptionUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [User.ROLE_ADMIN, User.ROLE_STAFF]
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'subscriptions/subscription_form.html'

    def get_success_url(self):
        return reverse('subscriptions:subscription_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Subscription updated successfully.")
        return super().form_valid(form)


class SubscriptionDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = [User.ROLE_ADMIN]
    model = Subscription
    template_name = 'subscriptions/subscription_confirm_delete.html'
    success_url = reverse_lazy('subscriptions:subscription_list')

    def form_valid(self, form):
        messages.success(self.request, "Subscription deleted.")
        return super().form_valid(form)


class SubscriptionStatusActionView(RoleRequiredMixin, View):
    allowed_roles = [User.ROLE_ADMIN, User.ROLE_STAFF]

    def post(self, request, pk, action, *args, **kwargs):
        subscription = get_object_or_404(Subscription, pk=pk)
        if action == 'activate':
            subscription.activate()
            messages.success(request, f"Subscription #{subscription.id} has been activated.")
        elif action == 'pause':
            subscription.pause()
            messages.warning(request, f"Subscription #{subscription.id} is now paused.")
        elif action == 'cancel':
            subscription.cancel()
            messages.error(request, f"Subscription #{subscription.id} has been cancelled.")
        else:
            messages.error(request, f"Unknown action: {action}")
        return redirect('subscriptions:subscription_detail', pk=subscription.pk)


class SubscriptionGenerateInvoiceView(RoleRequiredMixin, View):
    allowed_roles = [User.ROLE_ADMIN, User.ROLE_STAFF]

    def post(self, request, pk, *args, **kwargs):
        subscription = get_object_or_404(
            Subscription.objects.select_related('plan', 'discount'),
            pk=pk
        )
        try:
            invoice = generate_invoice_for_subscription(subscription)
            messages.success(
                request,
                f"Invoice {invoice.invoice_number} generated for ${invoice.total}! Due on {invoice.due_date}."
            )
            return redirect('billing:invoice_detail', pk=invoice.pk)
        except Exception as e:
            messages.error(request, f"Could not generate invoice: {str(e)}")
            return redirect('subscriptions:subscription_detail', pk=subscription.pk)
