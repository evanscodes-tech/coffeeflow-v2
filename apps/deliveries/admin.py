from django.contrib import admin 
from .models import CoffeeBatch 
 
@admin.register(CoffeeBatch) 
class CoffeeBatchAdmin(admin.ModelAdmin): 
    list_display = ('batch_code', 'farmer', 'cherry_weight_kg', 'dry_weight_kg', 'total_amount', 'payment_status', 'delivery_date') 
    list_filter = ('payment_status', 'quality_grade', 'delivery_date') 
    search_fields = ('batch_code', 'farmer__first_name', 'farmer__last_name') 
    readonly_fields = ('batch_code', 'dry_weight_kg', 'total_amount', 'created_at', 'updated_at') 
    list_per_page = 25 
