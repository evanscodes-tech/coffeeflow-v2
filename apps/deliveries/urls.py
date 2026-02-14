from django.urls import path 
from . import views 
 
app_name = 'deliveries' 
 
urlpatterns = [ 
    path('', views.delivery_list, name='list'), 
] 
