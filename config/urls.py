from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('catalog/', include('catalog.urls')),
    path('billing/', include('billing.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('', include('dashboard.urls')),
]

handler403 = 'config.views.custom_403_view'
handler404 = 'config.views.custom_404_view'
