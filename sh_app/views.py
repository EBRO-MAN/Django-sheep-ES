from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Sheep
from .form import AddRecordForm

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


def sheep_record(request, pk):
     if request.user.is_authenticated:
        #   Can look records
        sheep_record = Sheep.objects.get(ear_tag_number=pk)
        return render(request, 'record.html', {'sheep_record':sheep_record})
     
     else:
          messages.success(request, "You must be logged in to view records...")
          return redirect('home')
     

def delete_record(request, pk):
     if request.user.is_authenticated:
        delete_it = Sheep.objects.get(ear_tag_number=pk)
        delete_it.delete()

        messages.success(request, "Record deleted does successfully")
        return redirect('home')
     else:
        messages.success(request, "You must to loggedin to perform this")
        return redirect('home')

def add_record(request):
     form = AddRecordForm(request.POST or None)
     if request.user.is_authenticated:
          if request.method =="POST":
               if form.is_valid():
                    add_record = form.save()
                    messages.success(request, "Record Added...")
                    return redirect('home')
          return render(request, 'add_record.html', {'form':form})
     else:
          messages.success(request, "You must be logged in...")
          return redirect('home')
     
def update_record(request, pk):
     if request.user.is_authenticated:
          current_record = Sheep.objects.get(ear_tag_number=pk)
          form = AddRecordForm(request.POST or None, instance=current_record)
          if form.is_valid():
               form.save()
               messages.success(request, "Record has been updated!")
               return redirect('home')
          return render(request, 'update_record.html', {'form':form})
     else:
          messages.success(request, "You must be logged in...")
          return redirect('home')