from django.contrib import admin
from rest_framework import reverse
from .models import FarmerPayment

# TODO: Create Payment model first
# from .models import Payment
# 
# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ['id', 'farmer', 'amount', 'payment_date', 'status']
#     list_filter = ['status', 'payment_date']
#     search_fields = ['farmer__user__username', 'farmer__user__first_name']
#     readonly_fields = ['payment_date']
@admin.register(FarmerPayment)
class FarmerPaymentAdmin(admin.ModelAdmin):
    list_display = ['farmer', 'amount', 'payment_date', 'status', 'payment_method', 'transaction_id']
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = ['farmer__first_name', 'farmer__last_name', 'farmer__phone_number', 'transaction_id']
    readonly_fields = ['payment_date', 'completed_at']
    

    fieldsets = (
        ('Payment Details', {
            'fields': ('farmer', 'amount', 'payment_method', 'status', 'transaction_id', 'notes')
        }),
        ('Audit', {
            'fields': ('payment_date', 'completed_at', 'initiated_by')
        }),
    )