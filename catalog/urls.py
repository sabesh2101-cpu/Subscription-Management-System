from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    # Products
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/new/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),

    # Plans
    path('plans/', views.PlanListView.as_view(), name='plan_list'),
    path('plans/new/', views.PlanCreateView.as_view(), name='plan_create'),
    path('plans/<int:pk>/edit/', views.PlanUpdateView.as_view(), name='plan_update'),
    path('plans/<int:pk>/delete/', views.PlanDeleteView.as_view(), name='plan_delete'),
]
