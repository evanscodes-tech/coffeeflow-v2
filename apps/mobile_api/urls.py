from django.urls import path 
from . import views 
 
app_name = 'mobile_api' 
 
urlpatterns = [ 
    path('test/', views.test_api, name='test_api'), 
    path('farmer/dashboard/', views.farmer_dashboard, name='farmer_dashboard'), 
    path('farmer/deliveries/', views.farmer_deliveries, name='farmer_deliveries'), 
    path('farmer/profile/', views.farmer_profile, name='farmer_profile'), 
] 
