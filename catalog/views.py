from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from accounts.models import User
from accounts.permissions import RoleRequiredMixin
from .models import Product, SubscriptionPlan
from .forms import ProductForm, SubscriptionPlanForm


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        qs = Product.objects.prefetch_related('plans').order_by('-created_at')
        if not self.request.user.is_staff_role:
            qs = qs.filter(is_active=True)

        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(description__icontains=q))

        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            qs = qs.filter(is_active=True)
        elif status_filter == 'inactive' and self.request.user.is_staff_role:
            qs = qs.filter(is_active=False)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        qs = Product.objects.prefetch_related('plans')
        if not self.request.user.is_staff_role:
            qs = qs.filter(is_active=True)
        return qs


class ProductCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [User.ROLE_ADMIN]
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('catalog:product_list')

    def form_valid(self, form):
        messages.success(self.request, f"Product '{form.instance.name}' was created successfully.")
        return super().form_valid(form)


class ProductUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [User.ROLE_ADMIN]
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('catalog:product_list')

    def form_valid(self, form):
        messages.success(self.request, f"Product '{form.instance.name}' has been updated.")
        return super().form_valid(form)


class ProductDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = [User.ROLE_ADMIN]
    model = Product
    template_name = 'catalog/product_confirm_delete.html'
    success_url = reverse_lazy('catalog:product_list')

    def form_valid(self, form):
        messages.success(self.request, "Product deleted successfully.")
        return super().form_valid(form)


# Subscription Plans
class PlanListView(LoginRequiredMixin, ListView):
    model = SubscriptionPlan
    template_name = 'catalog/plan_list.html'
    context_object_name = 'plans'
    paginate_by = 12

    def get_queryset(self):
        qs = SubscriptionPlan.objects.select_related('product').order_by('product__name', 'price')
        if not self.request.user.is_staff_role:
            qs = qs.filter(is_active=True, product__is_active=True)

        cycle = self.request.GET.get('cycle')
        if cycle:
            qs = qs.filter(billing_cycle=cycle)

        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(product__name__icontains=q))

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cycle_filter'] = self.request.GET.get('cycle', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class PlanCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [User.ROLE_ADMIN]
    model = SubscriptionPlan
    form_class = SubscriptionPlanForm
    template_name = 'catalog/plan_form.html'
    success_url = reverse_lazy('catalog:plan_list')

    def form_valid(self, form):
        messages.success(self.request, f"Plan '{form.instance.name}' created successfully.")
        return super().form_valid(form)


class PlanUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [User.ROLE_ADMIN]
    model = SubscriptionPlan
    form_class = SubscriptionPlanForm
    template_name = 'catalog/plan_form.html'
    success_url = reverse_lazy('catalog:plan_list')

    def form_valid(self, form):
        messages.success(self.request, f"Plan '{form.instance.name}' updated successfully.")
        return super().form_valid(form)


class PlanDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = [User.ROLE_ADMIN]
    model = SubscriptionPlan
    template_name = 'catalog/plan_confirm_delete.html'
    success_url = reverse_lazy('catalog:plan_list')

    def form_valid(self, form):
        messages.success(self.request, "Plan deleted successfully.")
        return super().form_valid(form)
