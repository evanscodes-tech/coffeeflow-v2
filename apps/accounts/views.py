from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .forms import CustomUserCreationForm, UserProfileUpdateForm
from .models import CustomUser
from .otp_utils import generate_otp, is_otp_valid
from apps.farmers.models import FarmerProfile
from apps.deliveries.models import CoffeeBatch

import logging
logger = logging.getLogger(__name__)


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


def farmer_login(request):
    print("🔍 farmer_login view was called!") 
    """Step 1: Farmer enters username and password for OTP login"""
    
    if request.user.is_authenticated:
      return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_farmer():
            # Generate OTP
            otp = generate_otp()
            user.otp_code = otp
            user.otp_created_at = timezone.now()
            user.otp_verified = False
            user.save()
            
            # Send OTP via SMS (simulated for now)
            try:
                phone = user.farmer_profile.phone_number
                print(f"\n" + "="*60)
                print(f"📱 SIMULATED SMS - OTP for {username}")
                print(f"   Phone: {phone}")
                print(f"   OTP Code: {otp}")
                print(f"   Expires in: 5 minutes")
                print("="*60 + "\n")
                logger.info(f"OTP generated for {username}: {otp}")
            except Exception as e:
                logger.error(f"Failed to send OTP: {e}")
            
            # Store user ID in session for OTP verification
            request.session['otp_user_id'] = user.id
            
            return redirect('verify_otp')
        else:
            messages.error(request, 'Invalid username or password or you are not a farmer.')
    
    return render(request, 'accounts/farmer_login.html')


def verify_otp(request):
    """Step 2: Farmer enters OTP code to complete login"""
    
    user_id = request.session.get('otp_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please login again.')
        return redirect('farmer_login')
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found. Please login again.')
        return redirect('farmer_login')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        
        # Check if OTP is expired (5 minutes)
        if not is_otp_valid(user.otp_created_at):
            messages.error(request, 'OTP has expired. Please login again.')
            return redirect('farmer_login')
        
        # Verify OTP
        if otp_code == user.otp_code:
            user.otp_verified = True
            user.save()
            login(request, user)
            
            # Clear OTP session
            del request.session['otp_user_id']
            
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('profile')
        else:
            messages.error(request, 'Invalid OTP code. Please try again.')
    
    # Get masked phone number for display
    phone = ''
    try:
        full_phone = user.farmer_profile.phone_number
        if len(full_phone) >= 4:
            phone = '*' * (len(full_phone) - 4) + full_phone[-4:]
        else:
            phone = full_phone
    except:
        phone = 'your registered phone'
    
    return render(request, 'accounts/verify_otp.html', {'phone': phone})


def farmer_logout(request):
    """Custom logout for farmers"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('farmer_login')


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