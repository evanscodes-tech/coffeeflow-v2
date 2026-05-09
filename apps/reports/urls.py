from django.urls import path 
from . import views 
 
app_name = 'reports' 
 
urlpatterns = [ 
    path('', views.reports_index, name='index'),  # Reports dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('collection/', views.collection_report, name='collection_report'), 
    path('api/stats/', views.stats_api, name='api_stats'), 
    path('api/delivery-summary/', views.delivery_summary_chart, name='api_delivery_summary'), 
    path('api/quality-distribution/', views.quality_distribution_chart, name='api_quality_distribution'), 
    path('api/top-farmers/', views.top_farmers_table, name='api_top_farmers'), 
    path('api/harvest-prediction/', views.harvest_prediction, name='api_harvest_prediction'), 
    path('export/farmers/', views.export_farmers, name='export_farmers'),  # New: direct farmers export
    path('export/deliveries/', views.export_deliveries, name='export_deliveries'),  # New: direct deliveries export
    path('export/<str:report_type>/', views.export_report, name='export_report'), 
]