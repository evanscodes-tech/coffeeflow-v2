from django.shortcuts import render, redirect 
from django.contrib.auth import login 
from django.contrib.auth.decorators import login_required 
from django.contrib import messages 
from .forms import CustomUserCreationForm, UserProfileUpdateForm 
 
def home(request): 
    return render(request, 'home.html') 
 
def register(request): 
    if request.method == 'POST': 
        form = CustomUserCreationForm(request.POST) 
        if form.is_valid(): 
            user = form.save() 
            messages.success(request, 'Registration successful! Please log in.') 
            return redirect('login') 
    else: 
        form = CustomUserCreationForm() 
    return render(request, 'accounts/register.html', {'form': form}) 
 
@login_required 
def profile(request): 
    return render(request, 'accounts/profile.html', {'user': request.user}) 
 
@login_required 
def profile_edit(request): 
    if request.method == 'POST': 
        form = UserProfileUpdateForm(request.POST, instance=request.user) 
        if form.is_valid(): 
            form.save() 
            messages.success(request, 'Profile updated successfully!') 
            return redirect('profile') 
    else: 
        form = UserProfileUpdateForm(instance=request.user) 
    return render(request, 'accounts/profile_edit.html', {'form': form}) 
