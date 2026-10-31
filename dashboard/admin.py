from django.contrib import admin
from .models import MSMEStatistic


@admin.register(MSMEStatistic)
class MSMEStatisticAdmin(admin.ModelAdmin):
    list_display = ['state', 'sector', 'registered_units', 'year']
    list_filter = ['year', 'state', 'sector']
    search_fields = ['state', 'sector', 'notes']
