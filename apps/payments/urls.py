from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('pay/<str:farmer_id>/', views.pay_farmer, name='pay_farmer'),
    path('history/<str:farmer_id>/', views.payment_history, name='payment_history'),
    path('bulk/', views.bulk_payment, name='bulk_payment'),
    path('analytics/', views.payment_analytics, name='analytics'),
]