from django.http import JsonResponse 
from rest_framework.decorators import api_view, permission_classes 
from rest_framework.permissions import AllowAny, IsAuthenticated 
from rest_framework.response import Response 
from django.db.models import Sum, Count 
from django.utils import timezone 
from datetime import timedelta, datetime 
from apps.farmers.models import FarmerProfile 
from apps.deliveries.models import CoffeeBatch 
 
# Test endpoint - no authentication required 
@api_view(['GET']) 
@permission_classes([AllowAny]) 
def test_api(request): 
    return Response({ 
        "status": "success", 
        "message": "CoffeeFlow Mobile API is working!", 
        "version": "1.0", 
        "endpoints": [ 
            "/api/test/", 
            "/api/farmer/dashboard/", 
            "/api/farmer/deliveries/", 
            "/api/farmer/profile/" 
        ] 
    }) 
 
# Helper function to check if user is a farmer 
def get_farmer_profile(user): 
    try: 
        return FarmerProfile.objects.get(user=user) 
    except FarmerProfile.DoesNotExist: 
        return None 
 
# Farmer dashboard - requires authentication 
@api_view(['GET']) 
@permission_classes([IsAuthenticated]) 
def farmer_dashboard(request): 
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
 
# Farmer deliveries endpoint 
@api_view(['GET']) 
@permission_classes([IsAuthenticated]) 
def farmer_deliveries(request): 
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
 
# Farmer profile endpoint 
@api_view(['GET']) 
@permission_classes([IsAuthenticated]) 
def farmer_profile(request): 
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
