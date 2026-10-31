from functools import wraps
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles):
    """
    Decorator for views that checks whether a user has one of the allowed roles.
    Superusers always pass.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Please log in to access this page.")
                return redirect('accounts:login')
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to view this resource.")
        return _wrapped_view
    return decorator


class RoleRequiredMixin(AccessMixin):
    """
    CBV mixin that verifies the current user has one of the allowed roles.
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        roles = self.allowed_roles
        if isinstance(roles, str):
            roles = [roles]

        if request.user.role not in roles:
            raise PermissionDenied("You do not have permission to view this resource.")

        return super().dispatch(request, *args, **kwargs)
