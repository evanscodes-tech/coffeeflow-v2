from django.urls import path 
from . import views 
 
app_name = 'mobile_api' 
 
urlpatterns = [ 
    # Test endpoint
    path('test/', views.test_api, name='test_api'), 
    
    # Authentication endpoints
    path('auth/request-otp/', views.request_otp, name='request_otp'),
    path('auth/verify-otp/', views.verify_otp, name='verify_otp'),
    path('auth/logout/', views.logout, name='logout'),
    
    # Farmer endpoints (require authentication)
    path('farmer/dashboard/', views.farmer_dashboard, name='farmer_dashboard'), 
    path('farmer/deliveries/', views.farmer_deliveries, name='farmer_deliveries'), 
    path('farmer/profile/', views.farmer_profile, name='farmer_profile'), 
]