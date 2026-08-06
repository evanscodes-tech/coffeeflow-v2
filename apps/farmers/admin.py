from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import FarmerProfile


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = ['farmer_id_link', 'full_name', 'phone_number', 'farm_name', 'region', 'district', 'is_active']
    list_filter = ['region', 'district', 'is_active']
    search_fields = ['farmer_id', 'first_name', 'last_name', 'phone_number', 'national_id']
    ordering = ['farmer_id']

    def farmer_id_link(self, obj):
        if obj.farmer_id:
            url = reverse('farmers:farmer_detail', args=[obj.farmer_id])
            return format_html('<a href="{}"><strong>{}</strong></a>', url, obj.farmer_id)
        return "No ID"
    farmer_id_link.short_description = 'Farmer ID'