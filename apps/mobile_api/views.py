from .sms_utils import sms_service
from django.http import JsonResponse 
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated 
from rest_framework.response import Response 
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.db.models import Sum, Count 
from django.utils import timezone 
from datetime import timedelta, datetime 
from apps.farmers.models import FarmerProfile 
from apps.deliveries.models import CoffeeBatch 
from apps.accounts.models import CustomUser
from .models import MobileToken
import random
import string
import hashlib
import time

# OTP Store (temporary storage for OTP codes)
OTP_STORE = {}


# ========== CUSTOM TOKEN AUTHENTICATION ==========

class TokenAuthentication(BaseAuthentication):
    """Custom token authentication for mobile API using database"""
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        print(f"🔐 Auth header: {auth_header[:50] if auth_header else 'None'}")
        
        if not auth_header:
            return None
        
        # Extract token (supports both "Token xxx" and "Bearer xxx")
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        elif auth_header.startswith('Token '):
            token = auth_header[6:]
        
        if not token:
            print("❌ No token extracted from header")
            return None
        
        print(f"🔑 Token extracted: {token[:20]}...")
        
        # Look up token in database
        try:
            token_obj = MobileToken.objects.get(token=token)
            if not token_obj.is_valid():
                print(f"❌ Token expired for user: {token_obj.user.username}")
                token_obj.delete()
                raise AuthenticationFailed('Token expired')
            print(f"✅ Token valid for user: {token_obj.user.username}")
            return (token_obj.user, token)
        except MobileToken.DoesNotExist:
            print("❌ Token not found in database")
            raise AuthenticationFailed('Invalid token')


# ========== AUTHENTICATION ENDPOINTS ==========

@api_view(['POST'])
@permission_classes([AllowAny])
def request_otp(request):
    phone_number = request.data.get('phone_number')
    
    if not phone_number:
        return Response({"error": "Phone number required"}, status=400)
    
    try:
        farmer = FarmerProfile.objects.get(phone_number=phone_number)
    except FarmerProfile.DoesNotExist:
        return Response({"error": "No farmer found with this phone number"}, status=404)
    
    # Generate 6-digit OTP
    otp_code = ''.join(random.choices(string.digits, k=6))
    
    # Store OTP
    OTP_STORE[phone_number] = {
        'otp': otp_code,
        'expires_at': timezone.now() + timedelta(minutes=10),
        'farmer_id': farmer.id
    }
    
    print(f"========================================")
    print(f"📱 OTP for {farmer.full_name()}")
    print(f"📞 Phone: {phone_number}")
    print(f"🔐 OTP Code: {otp_code}")
    print(f"========================================")
    
    # Send SMS
    sms_sent, sms_message = sms_service.send_otp(phone_number, otp_code)
    
    if sms_sent:
        print(f"✅ {sms_message}")
    else:
        print(f"⚠️ SMS failed: {sms_message}")
    
    return Response({
        "success": True,
        "message": "OTP sent successfully",
        "debug_otp": otp_code,  # Remove in production
        "expires_in": 600
    }, status=200)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """Verify OTP and login farmer"""
    phone_number = request.data.get('phone_number')
    otp_code = request.data.get('otp_code')
    
    if not phone_number or not otp_code:
        return Response({
            "error": "Phone number and OTP code are required"
        }, status=400)
    
    # Check if OTP exists
    stored_data = OTP_STORE.get(phone_number)
    
    if not stored_data:
        return Response({
            "error": "No OTP request found. Please request a new OTP."
        }, status=400)
    
    # Check if OTP expired
    if timezone.now() > stored_data['expires_at']:
        if phone_number in OTP_STORE:
            del OTP_STORE[phone_number]
        return Response({
            "error": "OTP has expired. Please request a new OTP."
        }, status=400)
    
    # Check if OTP matches
    if stored_data['otp'] != otp_code:
        return Response({
            "error": "Invalid OTP code. Please try again."
        }, status=400)
    
    # OTP verified - clear it from store
    if phone_number in OTP_STORE:
        del OTP_STORE[phone_number]
    
    # Get farmer and user
    try:
        farmer = FarmerProfile.objects.get(phone_number=phone_number)
        user = farmer.user
    except FarmerProfile.DoesNotExist:
        return Response({
            "error": "Farmer not found"
        }, status=404)
    
    # Delete any existing tokens for this user
    MobileToken.objects.filter(user=user).delete()
    
    # Create new token (24 hours expiry)
    token_obj = MobileToken.create_token(user, expiry_hours=24)
    
    print(f"💾 Token created in database: {token_obj.token[:20]}... for user {user.username}")
    print(f"✅ Token expires at: {token_obj.expires_at}")
    
    return Response({
        "success": True,
        "token": token_obj.token,
        "user": {
            "id": farmer.id,
            "name": farmer.full_name(),
            "phone_number": farmer.phone_number,
            "farm_name": farmer.farm_name,
            "role": "farmer"
        }
    }, status=200)


@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    """Logout farmer - delete token"""
    auth_header = request.headers.get('Authorization', '')
    token = None
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    elif auth_header.startswith('Token '):
        token = auth_header[6:]
    
    if token:
        try:
            token_obj = MobileToken.objects.get(token=token)
            token_obj.delete()
            print(f"🗑️ Token deleted: {token[:20]}...")
        except MobileToken.DoesNotExist:
            print(f"⚠️ Token not found: {token[:20]}...")
    
    return Response({
        "success": True,
        "message": "Logged out successfully"
    }, status=200)


# ========== TEST ENDPOINT ==========

@api_view(['GET']) 
@permission_classes([AllowAny]) 
def test_api(request): 
    return Response({ 
        "status": "success", 
        "message": "CoffeeFlow Mobile API is working!", 
        "version": "1.0", 
        "endpoints": [ 
            "/api/test/", 
            "/api/auth/request-otp/",
            "/api/auth/verify-otp/",
            "/api/auth/logout/",
            "/api/farmer/dashboard/", 
            "/api/farmer/deliveries/", 
            "/api/farmer/profile/" 
        ] 
    }) 


# ========== HELPER FUNCTIONS ==========

def get_farmer_profile(user): 
    try: 
        return FarmerProfile.objects.get(user=user) 
    except FarmerProfile.DoesNotExist: 
        return None


# ========== FARMER ENDPOINTS ==========

@api_view(['GET']) 
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def farmer_dashboard(request): 
    print(f"📊 farmer_dashboard called - User: {request.user}")
    farmer = get_farmer_profile(request.user) 
    if not farmer: 
        return Response({ 
            "error": "No farmer profile found for this user" 
        }, status=404) 

    # Get current year data 
    current_year = timezone.now().year 

    # Calculate statistics 
    total_deliveries = CoffeeBatch.objects.filter(farmer=farmer).count() 
    total_kgs = CoffeeBatch.objects.filter(farmer=farmer).aggregate(total=Sum('cherry_weight_kg'))['total'] or 0 
    this_year_kgs = CoffeeBatch.objects.filter( 
        farmer=farmer, 
        delivery_date__year=current_year 
    ).aggregate(total=Sum('cherry_weight_kg'))['total'] or 0 

    # Get recent deliveries 
    recent_deliveries = CoffeeBatch.objects.filter( 
        farmer=farmer 
    ).order_by('-delivery_date')[:5] 

    deliveries_data = [] 
    for d in recent_deliveries: 
        deliveries_data.append({ 
            'id': d.id, 
            'batch_code': d.batch_code, 
            'date': d.delivery_date.strftime('%Y-%m-%d'), 
            'cherry_kg': float(d.cherry_weight_kg), 
            'dry_kg': float(d.dry_weight_kg), 
            'quality': d.get_quality_grade_display(), 
            'amount': float(d.total_amount), 
            'status': d.get_payment_status_display(), 
        }) 

    # Payment summary (calculated from deliveries) 
    pending_payments = CoffeeBatch.objects.filter( 
        farmer=farmer, 
        payment_status='pending' 
    ).aggregate(total=Sum('total_amount'))['total'] or 0 

    paid_payments = CoffeeBatch.objects.filter( 
        farmer=farmer, 
        payment_status='paid' 
    ).aggregate(total=Sum('total_amount'))['total'] or 0 

    return Response({ 
        "farmer": { 
            "id": farmer.id, 
            "name": farmer.full_name(), 
            "farm_name": farmer.farm_name, 
            "phone": farmer.phone_number, 
            "location": f"{farmer.village}, {farmer.district}", 
        }, 
        "stats": { 
            "total_deliveries": total_deliveries, 
            "total_kgs": float(total_kgs), 
            "this_year_kgs": float(this_year_kgs), 
            "pending_payments": float(pending_payments), 
            "paid_payments": float(paid_payments), 
        }, 
        "recent_deliveries": deliveries_data, 
    }) 


@api_view(['GET']) 
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def farmer_deliveries(request): 
    print(f"📦 farmer_deliveries called - User: {request.user}")
    farmer = get_farmer_profile(request.user) 
    if not farmer: 
        return Response({"error": "No farmer profile found"}, status=404) 

    # Get date filters from query params 
    year = request.GET.get('year') 
    month = request.GET.get('month') 

    deliveries = CoffeeBatch.objects.filter(farmer=farmer) 

    if year: 
        deliveries = deliveries.filter(delivery_date__year=year) 
    if month: 
        deliveries = deliveries.filter(delivery_date__month=month) 

    deliveries = deliveries.order_by('-delivery_date') 

    # Pagination 
    page = int(request.GET.get('page', 1)) 
    page_size = int(request.GET.get('page_size', 20)) 
    start = (page - 1) * page_size 
    end = start + page_size 

    deliveries_page = deliveries[start:end] 

    data = [] 
    for d in deliveries_page: 
        data.append({ 
            'id': d.id, 
            'batch_code': d.batch_code, 
            'date': d.delivery_date.strftime('%Y-%m-%d'), 
            'cherry_kg': float(d.cherry_weight_kg), 
            'dry_kg': float(d.dry_weight_kg), 
            'quality': d.get_quality_grade_display(), 
            'price_per_kg': float(d.price_per_kg), 
            'total_amount': float(d.total_amount), 
            'payment_status': d.get_payment_status_display(), 
            'payment_status_code': d.payment_status, 
        }) 

    return Response({ 
        'count': deliveries.count(), 
        'page': page, 
        'page_size': page_size, 
        'results': data, 
    }) 


@api_view(['GET']) 
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def farmer_profile(request): 
    print(f"👤 farmer_profile called - User: {request.user}")
    farmer = get_farmer_profile(request.user) 
    if not farmer: 
        return Response({"error": "No farmer profile found"}, status=404) 

    return Response({ 
        'id': farmer.id, 
        'first_name': farmer.first_name, 
        'last_name': farmer.last_name, 
        'full_name': farmer.full_name(), 
        'phone': farmer.phone_number, 
        'farm_name': farmer.farm_name, 
        'location': { 
            'region': farmer.get_region_display(), 
            'district': farmer.district, 
            'village': farmer.village, 
        }, 
        'farm_size': float(farmer.farm_size_acres), 
        'coffee_varieties': farmer.coffee_varieties, 
        'years_farming': farmer.years_farming, 
        'sms_notifications': farmer.sms_notifications, 
        'sms_language': farmer.sms_language, 
        'registered_since': farmer.registration_date.strftime('%Y-%m-%d'), 
    })