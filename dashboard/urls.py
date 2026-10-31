from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardIndexView.as_view(), name='index'),
    path('msme-statistics/', views.MSMEStatisticsView.as_view(), name='msme_statistics'),
]
