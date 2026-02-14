from django.contrib import admin 
from .models import FarmerProfile 
 
@admin.register(FarmerProfile) 
class FarmerProfileAdmin(admin.ModelAdmin): 
    list_display = ('first_name', 'last_name', 'phone_number', 'farm_name', 'region', 'is_active') 
    list_filter = ('region', 'is_active', 'registration_date') 
    search_fields = ('first_name', 'last_name', 'phone_number', 'national_id', 'farm_name') 
    list_per_page = 25 
