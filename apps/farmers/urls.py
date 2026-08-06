from django.urls import path 
from . import views 
 
app_name = 'farmers' 
 
urlpatterns = [ 
    path('', views.farmer_list, name='list'), 
    path('farmer/<str:farmer_id>/', views.farmer_detail, name='farmer_detail'),
    path('farmer/<str:farmer_id>/pdf/', views.farmer_statement_pdf, name='farmer_statement_pdf'),
    path('search/', views.search_farmer, name='search_farmer'),
] 
