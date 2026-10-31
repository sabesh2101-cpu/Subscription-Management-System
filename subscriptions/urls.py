from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.SubscriptionListView.as_view(), name='subscription_list'),
    path('new/', views.SubscriptionCreateView.as_view(), name='subscription_create'),
    path('<int:pk>/', views.SubscriptionDetailView.as_view(), name='subscription_detail'),
    path('<int:pk>/edit/', views.SubscriptionUpdateView.as_view(), name='subscription_update'),
    path('<int:pk>/delete/', views.SubscriptionDeleteView.as_view(), name='subscription_delete'),
    path('<int:pk>/status/<str:action>/', views.SubscriptionStatusActionView.as_view(), name='subscription_status_action'),
    path('<int:pk>/generate-invoice/', views.SubscriptionGenerateInvoiceView.as_view(), name='subscription_generate_invoice'),
]
