from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, ListView, View
from .models import User
from .forms import CustomerRegistrationForm, StyledAuthenticationForm, UserProfileForm, StaffUserCreationForm
from .permissions import RoleRequiredMixin


class RegisterView(CreateView):
    model = User
    form_class = CustomerRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('dashboard:index')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f"Welcome to Subscription Manager, {user.username}! Your customer account is active.")
        return redirect(self.success_url)


class CustomLoginView(LoginView):
    form_class = StyledAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('dashboard:index')

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().username}!")
        return super().form_valid(form)


class CustomLogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect('accounts:login')

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect('accounts:login')


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Your profile details have been updated.")
        return super().form_valid(form)


class UserListView(RoleRequiredMixin, ListView):
    allowed_roles = [User.ROLE_ADMIN]
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 15

    def get_queryset(self):
        qs = User.objects.all().order_by('-date_joined')
        role_filter = self.request.GET.get('role')
        if role_filter:
            qs = qs.filter(role=role_filter)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(username__icontains=q) | qs.filter(email__icontains=q) | qs.filter(company_name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_filter'] = self.request.GET.get('role', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class StaffCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [User.ROLE_ADMIN]
    model = User
    form_class = StaffUserCreationForm
    template_name = 'accounts/staff_create.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, f"Team member {user.username} ({user.get_role_display()}) created successfully.")
        return redirect(self.success_url)
