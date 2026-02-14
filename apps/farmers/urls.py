from django.urls import path 
from . import views 
 
app_name = 'farmers' 
 
urlpatterns = [ 
    path('', views.farmer_list, name='list'), 
] 
