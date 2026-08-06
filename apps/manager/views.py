from django.shortcuts import render 
from django.contrib.admin.views.decorators import staff_member_required 
from django.db.models import Sum 
from apps.farmers.models import FarmerProfile 
from apps.deliveries.models import CoffeeBatch 
from apps.payments.models import FarmerPayment 
from datetime import timedelta 
from django.utils import timezone 
 
@staff_member_required 
def manager_dashboard(request): 
    # Only allow manager or admin 
    if request.user.role not in ['manager', 'admin']: 
        return render(request, 'manager/access_denied.html') 
 
    total_farmers = FarmerProfile.objects.count() 
    total_deliveries = CoffeeBatch.objects.count() 
    total_kgs = CoffeeBatch.objects.aggregate(total=Sum('cherry_weight_kg'))['total'] or 0 
 
    today = timezone.now().date() 
    today_deliveries = CoffeeBatch.objects.filter(delivery_date=today) 
    today_count = today_deliveries.count() 
    today_kgs = today_deliveries.aggregate(total=Sum('cherry_weight_kg'))['total'] or 0 
 
    total_paid = FarmerPayment.objects.filter(status='success').aggregate(total=Sum('amount'))['total'] or 0 
    total_pending = FarmerPayment.objects.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0 
 
    recent_deliveries = CoffeeBatch.objects.all().order_by('-delivery_date')[:10] 
    recent_payments = FarmerPayment.objects.all().order_by('-payment_date')[:10] 
 
    context = { 
        'total_farmers': total_farmers, 
        'total_deliveries': total_deliveries, 
        'total_kgs': total_kgs, 
        'today_count': today_count, 
        'today_kgs': today_kgs, 
        'total_paid': total_paid, 
        'total_pending': total_pending, 
        'recent_deliveries': recent_deliveries, 
        'recent_payments': recent_payments, 
    } 
    return render(request, 'manager/dashboard.html', context) 
