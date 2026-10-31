from decimal import Decimal
from django import forms
from django.utils import timezone
from .models import Discount, Invoice, Payment
from subscriptions.models import Subscription


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ['code', 'type', 'value', 'valid_from', 'valid_to', 'usage_limit', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. SUMMER20'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'valid_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valid_to': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'usage_limit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Optional limit'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['subscription', 'issue_date', 'due_date', 'subtotal', 'discount_amount', 'tax_amount', 'status', 'notes']
        widgets = {
            'subscription': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'subtotal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subscription'].queryset = Subscription.objects.select_related('customer', 'plan').all()


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'method', 'reference', 'paid_on', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01', 'placeholder': 'Amount in USD'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. TXN-998822 or UPI ref'}),
            'paid_on': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional memo'}),
        }

    def __init__(self, invoice=None, *args, **kwargs):
        self.invoice = invoice
        super().__init__(*args, **kwargs)
        if invoice:
            self.fields['amount'].initial = invoice.balance_due
        if not self.initial.get('paid_on'):
            self.fields['paid_on'].initial = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and self.invoice:
            balance = self.invoice.balance_due
            if amount > balance:
                raise forms.ValidationError(f"Payment amount (${amount}) exceeds invoice balance due (${balance}).")
        return amount
