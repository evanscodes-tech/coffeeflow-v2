from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'staff_portal'

urlpatterns = [
    path('', login_required(views.dashboard), name='dashboard'),
    path('register-farmer/', login_required(views.register_farmer), name='register_farmer'),
    path('record-delivery/', login_required(views.record_delivery), name='record_delivery'),
    path('farmers/', login_required(views.farmer_list), name='farmer_list'),
]