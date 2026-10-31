from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Discounts
    path('discounts/', views.DiscountListView.as_view(), name='discount_list'),
    path('discounts/new/', views.DiscountCreateView.as_view(), name='discount_create'),
    path('discounts/<int:pk>/edit/', views.DiscountUpdateView.as_view(), name='discount_update'),
    path('discounts/<int:pk>/delete/', views.DiscountDeleteView.as_view(), name='discount_delete'),
    path('discounts/check-code/', views.DiscountCheckView.as_view(), name='discount_check'),

    # Invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/new/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/print/', views.InvoicePrintView.as_view(), name='invoice_print'),
    path('invoices/<int:pk>/record-payment/', views.InvoiceRecordPaymentView.as_view(), name='invoice_record_payment'),

    # Payments
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
]
