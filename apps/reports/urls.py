from django.urls import path 
from . import views 
 
app_name = 'reports' 
 
urlpatterns = [ 
    path('', views.dashboard, name='dashboard'), 
    path('api/stats/', views.stats_api, name='api_stats'), 
    path('api/delivery-summary/', views.delivery_summary_chart, name='api_delivery_summary'), 
    path('api/quality-distribution/', views.quality_distribution_chart, name='api_quality_distribution'), 
    path('api/top-farmers/', views.top_farmers_table, name='api_top_farmers'), 
    path('api/harvest-prediction/', views.harvest_prediction, name='api_harvest_prediction'), 
] 
