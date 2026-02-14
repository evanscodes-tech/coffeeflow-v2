from django.shortcuts import render 
from django.contrib.auth.decorators import login_required 
from .models import CoffeeBatch 
 
@login_required 
def delivery_list(request): 
    deliveries = CoffeeBatch.objects.all() 
    return render(request, 'deliveries/list.html', {'deliveries': deliveries}) 
