from django.http import JsonResponse 
from rest_framework.decorators import api_view, permission_classes 
from rest_framework.permissions import AllowAny, IsAuthenticated 
from rest_framework.response import Response 
 
# Test endpoint - no authentication required 
@api_view(['GET']) 
@permission_classes([AllowAny]) 
def test_api(request): 
    return Response({ 
        "status": "success", 
        "message": "CoffeeFlow Mobile API is working!", 
        "version": "1.0" 
    }) 
 
# Farmer dashboard endpoint - requires authentication 
@api_view(['GET']) 
@permission_classes([IsAuthenticated]) 
def farmer_dashboard(request): 
    return Response({ 
        "message": "Farmer dashboard endpoint", 
        "user": request.user.username 
    }) 
 
# Farmer deliveries endpoint 
@api_view(['GET']) 
@permission_classes([IsAuthenticated]) 
def farmer_deliveries(request): 
    return Response({ 
        "message": "Farmer deliveries endpoint", 
        "deliveries": [] 
    }) 
 
# Farmer payments endpoint 
@api_view(['GET']) 
@permission_classes([IsAuthenticated]) 
def farmer_payments(request): 
    return Response({ 
        "message": "Farmer payments endpoint", 
        "payments": [] 
    }) 
