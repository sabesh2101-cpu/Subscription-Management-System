from django import forms
from django.utils import timezone
from .models import Subscription
from accounts.models import User
from catalog.models import SubscriptionPlan
from billing.models import Discount


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['customer', 'plan', 'start_date', 'next_billing_date', 'status', 'discount', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_billing_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'discount': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Internal notes or special terms'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = User.objects.filter(role=User.ROLE_CUSTOMER).order_by('username')
        self.fields['plan'].queryset = SubscriptionPlan.objects.filter(is_active=True).select_related('product').order_by('product__name', 'price')
        self.fields['discount'].queryset = Discount.objects.filter(is_active=True).order_by('code')
        self.fields['discount'].required = False
        self.fields['next_billing_date'].required = False
        if not self.initial.get('start_date'):
            self.fields['start_date'].initial = timezone.now().date()
