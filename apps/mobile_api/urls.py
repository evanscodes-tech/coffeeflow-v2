from django.urls import path 
from . import views 
 
app_name = 'mobile_api' 
 
urlpatterns = [ 
    # Add API endpoints here later 
    path('test/', views.test_api, name='test_api'), 
] 
