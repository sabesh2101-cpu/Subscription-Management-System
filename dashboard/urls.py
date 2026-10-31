from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardIndexView.as_view(), name='index'),
    path('admin-hub/', views.AdminHubView.as_view(), name='admin_hub'),
    path('staff-workbench/', views.StaffWorkbenchView.as_view(), name='staff_workbench'),
    path('msme-statistics/', views.MSMEStatisticsView.as_view(), name='msme_statistics'),
]
