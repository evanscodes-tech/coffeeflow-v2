from django.shortcuts import render, get_object_or_404 
from django.contrib.auth.decorators import login_required 
from django.contrib.admin.views.decorators import staff_member_required 
from .models import FarmerProfile 
 
@login_required 
def farmer_list(request): 
    farmers = FarmerProfile.objects.all() 
    return render(request, 'farmers/list.html', {'farmers': farmers}) 
 
@login_required 
def farmer_detail(request, pk): 
    farmer = get_object_or_404(FarmerProfile, pk=pk) 
    return render(request, 'farmers/detail.html', {'farmer': farmer}) 
