from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from apps.farmers.models import FarmerProfile
from apps.payments.models import FarmerPayment
from apps.payments.mpesa_utils import MpesaClient
import json
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta

@staff_member_required
def pay_farmer(request, farmer_id):
    """
    Pay a farmer via M-Pesa
    """
    farmer = get_object_or_404(FarmerProfile, farmer_id=farmer_id)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        phone_number = request.POST.get('phone_number')
        payment_method = request.POST.get('payment_method', 'mpesa')
        
        if not amount or float(amount) <= 0:
            messages.error(request, 'Please enter a valid amount')
            return redirect('farmers:farmer_detail', farmer_id=farmer.farmer_id)
        
        # Use farmer's phone number if not provided
        if not phone_number:
            phone_number = farmer.phone_number
        
        # Create payment record
        payment = FarmerPayment.objects.create(
            farmer=farmer,
            amount=amount,
            status='pending',
            payment_method=payment_method,
            initiated_by=request.user,
            notes=f"Payment initiated by {request.user.username}"
        )
        
        # If M-Pesa, process payment
        if payment_method == 'mpesa':
            client = MpesaClient()
            response = client.b2c_payment(phone_number, amount)
            
            if response and response.get('ResponseCode') == '0':
                payment.status = 'processing'
                payment.transaction_id = response.get('ConversationID', '')
                payment.save()
                messages.success(request, f'✅ Payment of KES {amount} sent to {farmer.full_name()}')
            else:
                payment.status = 'failed'
                payment.notes = f"Failed: {response.get('errorMessage', 'Unknown error')}"
                payment.save()
                messages.error(request, f'❌ Payment failed: {response.get("errorMessage", "Unknown error")}')
        else:
            # Manual payment (Cash/Bank) - mark as success
            payment.status = 'success'
            payment.completed_at = timezone.now()
            payment.save()
            messages.success(request, f'✅ Payment of KES {amount} recorded for {farmer.full_name()}')
        
        return redirect('farmers:farmer_detail', farmer_id=farmer.farmer_id)
    
    # GET request - show payment form
    context = {
        'farmer': farmer,
        'default_phone': farmer.phone_number,
    }
    return render(request, 'payments/pay_farmer.html', context)


@staff_member_required
def payment_history(request, farmer_id):
    """
    View payment history for a farmer
    """
    farmer = get_object_or_404(FarmerProfile, farmer_id=farmer_id)
    payments = FarmerPayment.objects.filter(farmer=farmer).order_by('-payment_date')
    
    context = {
        'farmer': farmer,
        'payments': payments,
    }
    return render(request, 'payments/payment_history.html', context)

@staff_member_required
def bulk_payment(request):
    """Pay multiple farmers at once"""
    farmers = FarmerProfile.objects.filter(is_active=True).order_by('farmer_id')
    
    if request.method == 'POST':
        farmer_ids = request.POST.getlist('farmer_ids')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method', 'mpesa')
        
        if not farmer_ids:
            messages.error(request, 'Please select at least one farmer.')
            return redirect('payments:bulk_payment')
        
        if not amount or float(amount) <= 0:
            messages.error(request, 'Please enter a valid amount.')
            return redirect('payments:bulk_payment')
        
        selected_farmers = FarmerProfile.objects.filter(id__in=farmer_ids)
        success_count = 0
        failed_count = 0
        
        for farmer in selected_farmers:
            payment = FarmerPayment.objects.create(
                farmer=farmer,
                amount=amount,
                status='pending',
                payment_method=payment_method,
                initiated_by=request.user,
                notes=f"Bulk payment initiated by {request.user.username}"
            )
            
            if payment_method == 'mpesa':
                client = MpesaClient()
                response = client.b2c_payment(farmer.phone_number, amount)
                
                if response and response.get('ResponseCode') == '0':
                    payment.status = 'processing'
                    payment.transaction_id = response.get('ConversationID', '')
                    payment.save()
                    success_count += 1
                else:
                    payment.status = 'failed'
                    payment.notes = f"Failed: {response.get('errorMessage', 'Unknown error')}"
                    payment.save()
                    failed_count += 1
            else:
                payment.status = 'success'
                payment.completed_at = timezone.now()
                payment.save()
                success_count += 1
        
        messages.success(
            request, 
            f'✅ Bulk payment completed! {success_count} successful, {failed_count} failed.'
        )
        return redirect('payments:bulk_payment')
    
    context = {
        'farmers': farmers,
        'total_farmers': farmers.count(),
    }
    return render(request, 'payments/bulk_payment.html', context)
@staff_member_required
def payment_analytics(request):
    """Payment analytics dashboard"""
    
    total_paid = FarmerPayment.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_success = FarmerPayment.objects.filter(status='success').aggregate(total=Sum('amount'))['total'] or 0
    total_pending = FarmerPayment.objects.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    total_failed = FarmerPayment.objects.filter(status='failed').aggregate(total=Sum('amount'))['total'] or 0
    
    payment_count = FarmerPayment.objects.count()
    success_count = FarmerPayment.objects.filter(status='success').count()
    pending_count = FarmerPayment.objects.filter(status='pending').count()
    failed_count = FarmerPayment.objects.filter(status='failed').count()
    
    # Today's payments
    today = timezone.now().date()
    today_payments = FarmerPayment.objects.filter(payment_date__date=today)
    today_total = today_payments.aggregate(total=Sum('amount'))['total'] or 0
    today_count = today_payments.count()
    
    # Monthly payments (last 30 days)
    month_ago = timezone.now() - timedelta(days=30)
    month_payments = FarmerPayment.objects.filter(payment_date__gte=month_ago)
    month_total = month_payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent payments
    recent_payments = FarmerPayment.objects.all().order_by('-payment_date')[:10]
    
    context = {
        'total_paid': total_paid,
        'total_success': total_success,
        'total_pending': total_pending,
        'total_failed': total_failed,
        'payment_count': payment_count,
        'success_count': success_count,
        'pending_count': pending_count,
        'failed_count': failed_count,
        'today_total': today_total,
        'today_count': today_count,
        'month_total': month_total,
        'recent_payments': recent_payments,
    }
    return render(request, 'payments/analytics.html', context)
