from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q
from django.utils import timezone
from accounts.models import User
from accounts.permissions import RoleRequiredMixin
from .models import Discount, Invoice, Payment
from .forms import DiscountForm, InvoiceForm, PaymentForm
from .services import record_payment


# Discounts
class DiscountListView(RoleRequiredMixin, ListView):
    allowed_roles = [User.ROLE_ADMIN, User.ROLE_STAFF]
    model = Discount
    template_name = 'billing/discount_list.html'
    context_object_name = 'discounts'
    paginate_by = 12

    def get_queryset(self):
        qs = Discount.objects.all().order_by('-created_at')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(code__icontains=q)
        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            qs = qs.filter(is_active=True)
        elif status_filter == 'inactive':
            qs = qs.filter(is_active=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class DiscountCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [User.ROLE_ADMIN]
    model = Discount
    form_class = DiscountForm
    template_name = 'billing/discount_form.html'
    success_url = reverse_lazy('billing:discount_list')

    def form_valid(self, form):
        messages.success(self.request, f"Discount '{form.instance.code}' created successfully.")
        return super().form_valid(form)


class DiscountUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [User.ROLE_ADMIN]
    model = Discount
    form_class = DiscountForm
    template_name = 'billing/discount_form.html'
    success_url = reverse_lazy('billing:discount_list')

    def form_valid(self, form):
        messages.success(self.request, f"Discount '{form.instance.code}' updated.")
        return super().form_valid(form)


class DiscountDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = [User.ROLE_ADMIN]
    model = Discount
    template_name = 'billing/discount_confirm_delete.html'
    success_url = reverse_lazy('billing:discount_list')

    def form_valid(self, form):
        messages.success(self.request, "Discount deleted.")
        return super().form_valid(form)


class DiscountCheckView(LoginRequiredMixin, View):
    """AJAX check for discount codes."""
    def get(self, request, *args, **kwargs):
        code = request.GET.get('code', '').strip().upper()
        subtotal_str = request.GET.get('subtotal', '0')
        try:
            subtotal = Decimal(subtotal_str)
        except Exception:
            subtotal = Decimal('0.00')

        if not code:
            return JsonResponse({'valid': False, 'message': 'Please enter a discount code.'})

        try:
            discount = Discount.objects.get(code=code)
            is_valid, msg = discount.is_currently_valid()
            if not is_valid:
                return JsonResponse({'valid': False, 'message': msg})
            discount_amount = discount.calculate_discount_amount(subtotal)
            return JsonResponse({
                'valid': True,
                'code': discount.code,
                'type': discount.get_type_display(),
                'value': str(discount.value),
                'discount_amount': str(discount_amount),
                'final_total': str(max(Decimal('0.00'), subtotal - discount_amount)),
                'message': f"Valid! {discount.get_type_display()} discount of {discount.value}."
            })
        except Discount.DoesNotExist:
            return JsonResponse({'valid': False, 'message': 'Discount code does not exist.'})


# Invoices
class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'billing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 12

    def get_queryset(self):
        qs = Invoice.objects.select_related('subscription', 'subscription__customer', 'subscription__plan')
        if self.request.user.is_customer_role:
            qs = qs.filter(subscription__customer=self.request.user)

        status_filter = self.request.GET.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(invoice_number__icontains=q) |
                Q(subscription__customer__username__icontains=q) |
                Q(subscription__customer__company_name__icontains=q) |
                Q(subscription__plan__name__icontains=q)
            )
        return qs.order_by('-issue_date', '-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'billing/invoice_detail.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        qs = Invoice.objects.select_related(
            'subscription',
            'subscription__customer',
            'subscription__plan',
            'subscription__plan__product',
            'subscription__discount'
        ).prefetch_related('payments')

        if self.request.user.is_customer_role:
            qs = qs.filter(subscription__customer=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_staff_role:
            context['payment_form'] = PaymentForm(invoice=self.object)
        return context


class InvoicePrintView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'billing/invoice_print.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        qs = Invoice.objects.select_related(
            'subscription',
            'subscription__customer',
            'subscription__plan',
            'subscription__plan__product',
            'subscription__discount'
        ).prefetch_related('payments')

        if self.request.user.is_customer_role:
            qs = qs.filter(subscription__customer=self.request.user)
        return qs


class InvoiceCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [User.ROLE_ADMIN, User.ROLE_STAFF]
    model = Invoice
    form_class = InvoiceForm
    template_name = 'billing/invoice_form.html'

    def get_success_url(self):
        return reverse('billing:invoice_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f"Invoice {form.instance.invoice_number or 'created'} successfully.")
        return super().form_valid(form)


class InvoiceRecordPaymentView(RoleRequiredMixin, View):
    allowed_roles = [User.ROLE_ADMIN, User.ROLE_STAFF]

    def post(self, request, pk, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=pk)
        form = PaymentForm(invoice=invoice, data=request.POST)
        if form.is_valid():
            try:
                payment = record_payment(
                    invoice=invoice,
                    amount=form.cleaned_data['amount'],
                    method=form.cleaned_data['method'],
                    reference=form.cleaned_data.get('reference', ''),
                    paid_on=form.cleaned_data.get('paid_on'),
                    notes=form.cleaned_data.get('notes', '')
                )
                messages.success(request, f"Payment of ${payment.amount} recorded! Invoice status updated to {invoice.get_status_display()}.")
            except Exception as e:
                messages.error(request, f"Error processing payment: {str(e)}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field.capitalize()}: {err}")
        return redirect('billing:invoice_detail', pk=invoice.pk)


# Payments
class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'billing/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 15

    def get_queryset(self):
        qs = Payment.objects.select_related(
            'invoice',
            'invoice__subscription',
            'invoice__subscription__customer'
        )
        if self.request.user.is_customer_role:
            qs = qs.filter(invoice__subscription__customer=self.request.user)

        method = self.request.GET.get('method')
        if method:
            qs = qs.filter(method=method)

        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(invoice__invoice_number__icontains=q) |
                Q(reference__icontains=q) |
                Q(invoice__subscription__customer__username__icontains=q)
            )

        return qs.order_by('-paid_on', '-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['method_filter'] = self.request.GET.get('method', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context
