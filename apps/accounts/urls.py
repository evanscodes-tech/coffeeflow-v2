from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    
    # Use custom logout
    path('logout/', views.custom_logout, name='logout'),
    
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('register/', views.register, name='register'),
     path('farmer-login/', views.farmer_login, name='farmer_login'),
     path('verify-otp/', views.verify_otp, name='verify_otp'),
     path('farmer-logout/', views.farmer_logout, name='farmer_logout'),


]