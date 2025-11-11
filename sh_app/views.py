from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Sheep


def home(request):
    sheeps = Sheep.objects.all()

    # Check to see if logging in
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        # Authenticate
        user = authenticate(request, username = username, password = password)
        if user is not None:
            login(request, user)
            messages.success(request, "You Have Been Logged in!")
            return redirect('home')
        else:
                messages.success(request,"There was an Error Logging In, Please Try Again...")
                return redirect('home')
    else:
            return render(request, 'home.html', {'sheeps':sheeps})
    

def logout_user(request):
    logout(request)
    messages.success(request, "You Have Been Logged Out...")
    return redirect('home')