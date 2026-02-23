from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .forms import CustomUserCreationForm, UserProfileUpdateForm
from apps.farmers.models import FarmerProfile
from apps.deliveries.models import CoffeeBatch

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Registration successful! Welcome {user.username}. Please log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@require_POST
@csrf_protect
def custom_logout(request):
    """Custom logout view that accepts POST requests"""
    logout(request)
    return redirect('/')

@login_required
def profile(request):
    # Get the farmer profile for the logged-in user
    try:
        farmer = FarmerProfile.objects.get(user=request.user)
        
        # Get all deliveries for this farmer
        deliveries = CoffeeBatch.objects.filter(farmer=farmer).order_by('-delivery_date')
        
        # Calculate statistics
        total_deliveries = deliveries.count()
        total_kgs = deliveries.aggregate(total=Sum('cherry_weight_kg'))['total'] or 0
        total_paid = deliveries.filter(payment_status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
        total_pending = deliveries.filter(payment_status='pending').aggregate(total=Sum('total_amount'))['total'] or 0
        
        context = {
            'user': request.user,
            'farmer': farmer,
            'deliveries': deliveries[:10],  # Last 10 deliveries
            'total_deliveries': total_deliveries,
            'total_kgs': total_kgs,
            'total_paid': total_paid,
            'total_pending': total_pending,
        }
    except FarmerProfile.DoesNotExist:
        # User is logged in but doesn't have a farmer profile
        context = {
            'user': request.user,
            'no_farmer_profile': True
        }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})