from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth import get_user_model
from apps.farmers.models import FarmerProfile
from apps.deliveries.models import CoffeeBatch

User = get_user_model()


# Helper function to check if user has staff or admin access
def has_staff_access(user):
    return user.is_authenticated and (user.role in ['super_admin', 'staff'] or user.is_staff or user.is_superuser)


@login_required
def dashboard(request):
    """Staff dashboard - shows today's activities"""
    
    # Check if user has staff or super admin role
    if not has_staff_access(request.user):
        messages.error(request, 'You do not have access to this page.')
        return redirect('home')
    
    today = timezone.now().date()
    
    # Today's deliveries
    today_deliveries = CoffeeBatch.objects.filter(delivery_date=today).order_by('-created_at')
    today_total_kgs = today_deliveries.aggregate(total=Sum('cherry_weight_kg'))['total'] or 0
    today_count = today_deliveries.count()
    
    # Total farmers
    total_farmers = FarmerProfile.objects.count()
    
    context = {
        'today_deliveries': today_deliveries[:10],
        'today_total_kgs': today_total_kgs,
        'today_count': today_count,
        'total_farmers': total_farmers,
    }
    return render(request, 'staff_portal/dashboard.html', context)


@login_required
def register_farmer(request):
    """Register a new farmer (create user account + farmer profile)"""
    
    # Check permission
    if not has_staff_access(request.user):
        messages.error(request, 'You do not have permission to register farmers.')
        return redirect('staff_portal:dashboard')
    
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email', '')
        phone_number = request.POST.get('phone_number')
        national_id = request.POST.get('national_id')
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already exists. Please choose another.')
            return render(request, 'staff_portal/register_farmer.html')
        
        # Check if phone number exists
        if FarmerProfile.objects.filter(phone_number=phone_number).exists():
            messages.error(request, f'Phone number "{phone_number}" is already registered.')
            return render(request, 'staff_portal/register_farmer.html')
        
        # Check if national ID exists
        if FarmerProfile.objects.filter(national_id=national_id).exists():
            messages.error(request, f'National ID "{national_id}" is already registered.')
            return render(request, 'staff_portal/register_farmer.html')
        
        # Create the user account
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                role='farmer'
            )
            
            # Create farmer profile
            farmer = FarmerProfile.objects.create(
                user=user,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                national_id=national_id,
                phone_number=phone_number,
                alt_phone_number=request.POST.get('alt_phone_number', ''),
                farm_name=request.POST.get('farm_name'),
                region=request.POST.get('region'),
                district=request.POST.get('district'),
                village=request.POST.get('village'),
                farm_size_acres=request.POST.get('farm_size_acres', 0),
                coffee_varieties=request.POST.get('coffee_varieties', ''),
                years_farming=request.POST.get('years_farming', 1),
                sms_notifications=request.POST.get('sms_notifications') == 'on',
                sms_language=request.POST.get('sms_language', 'en'),
                registered_by=request.user,
                gender=request.POST.get('gender', '')
            )
            
            messages.success(request, f'✅ Farmer {farmer.full_name()} registered successfully!')
            messages.info(request, f'📱 Farmer can login with Username: {username} and Password: {password}')
            
            return redirect('staff_portal:dashboard')
            
        except Exception as e:
            messages.error(request, f'Error creating farmer: {str(e)}')
            return render(request, 'staff_portal/register_farmer.html')
    
    return render(request, 'staff_portal/register_farmer.html')


@login_required
def record_delivery(request):
    """Record a coffee delivery"""
    
    if not has_staff_access(request.user):
        messages.error(request, 'You do not have permission to record deliveries.')
        return redirect('staff_portal:dashboard')
    
    if request.method == 'POST':
        farmer_id = request.POST.get('farmer_id')
        cherry_weight_kg = request.POST.get('cherry_weight_kg')
        quality_grade = request.POST.get('quality_grade', 'standard')
        price_per_kg = request.POST.get('price_per_kg', 120)
        
        try:
            # Convert to proper types
            farmer = get_object_or_404(FarmerProfile, id=int(farmer_id))
            cherry_weight = float(cherry_weight_kg)
            price = float(price_per_kg)
            
            # Create delivery (auto-calculates dry weight and total)
            delivery = CoffeeBatch.objects.create(
                farmer=farmer,
                cherry_weight_kg=cherry_weight,
                quality_grade=quality_grade,
                price_per_kg=price,
                recorded_by=request.user
            )
            
            messages.success(request, f'✅ Delivery recorded! {cherry_weight}kg from {farmer.full_name()}')
            return redirect('staff_portal:dashboard')
            
        except ValueError:
            messages.error(request, '❌ Invalid weight value. Please enter a number (e.g., 500).')
        except Exception as e:
            messages.error(request, f'❌ Error recording delivery: {str(e)}')
    
    farmers = FarmerProfile.objects.filter(is_active=True).order_by('first_name')
    return render(request, 'staff_portal/record_delivery.html', {'farmers': farmers})


@login_required
def farmer_list(request):
    """List all farmers"""
    
    if not has_staff_access(request.user):
        messages.error(request, 'You do not have permission to view farmers.')
        return redirect('staff_portal:dashboard')
    
    farmers = FarmerProfile.objects.all().order_by('first_name')
    return render(request, 'staff_portal/farmer_list.html', {'farmers': farmers})