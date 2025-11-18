# from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
# from .models import Sheep
from .form import AddRecordForm
# from .services import get_available_rams, get_available_ewes, get_compatible_ewes
# from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from .models import Sheep, BreedingCycle
from .services import (get_available_rams, get_available_ewes, get_compatible_ewes, 
                      get_family_relationship, check_breed_compatibility, check_for_inbreeding,
                      predict_lamb_breed, get_breed_restrictions, get_breed_compatibility_info)
import json

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
     

@login_required
def breeding_selection(request):
    """Main breeding selection view with breed compatibility"""
    rams = get_available_rams()
    ewes = get_available_ewes()
    
    selected_ram_id = request.GET.get('ram_id')
    selected_ram = None
    compatible_ewes = []
    breed_compatibility_info = None
    incompatible_ewes_info = []
    
    if selected_ram_id:
        try:
            selected_ram = Sheep.objects.get(ear_tag_number=selected_ram_id)
            compatible_ewes = get_compatible_ewes(selected_ram)
            breed_compatibility_info = get_breed_compatibility_info(selected_ram)
            
            # Get information about incompatible ewes for debugging
            all_ewes = get_available_ewes()
            for ewe in all_ewes:
                if ewe not in compatible_ewes:
                    # Check if it's due to breed or family
                    breed_ok = check_breed_compatibility(selected_ram, ewe)
                    family_ok = check_for_inbreeding(ewe, selected_ram)
                    
                    if not breed_ok:
                        incompatible_ewes_info.append({
                            'ewe': ewe.ear_tag_number,
                            'breed': ewe.breed,
                            'reason': f"Breed incompatibility: {selected_ram.breed} ram cannot mate with {ewe.breed} ewe"
                        })
                    elif not family_ok:
                        relationships = get_family_relationship(ewe, selected_ram)
                        incompatible_ewes_info.append({
                            'ewe': ewe.ear_tag_number,
                            'breed': ewe.breed,
                            'reason': f"Family relationship: {', '.join(relationships)}"
                        })
            
        except Sheep.DoesNotExist:
            pass
    
    context = {
        'rams': rams,
        'ewes': ewes,
        'selected_ram': selected_ram,
        'compatible_ewes': compatible_ewes,
        'breed_compatibility_info': breed_compatibility_info,
        'incompatible_ewes_info': incompatible_ewes_info,
    }
    
    return render(request, 'breeding.html', context)

@login_required
def create_breeding_cycle(request):
    """Handle breeding cycle creation with breed prediction"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ewe_id = data.get('ewe_id')
            ram_id = data.get('ram_id')
            start_date = data.get('start_date')
            
            ewe = Sheep.objects.get(ear_tag_number=ewe_id)
            ram = Sheep.objects.get(ear_tag_number=ram_id)
            
            # Double-check breed compatibility
            from .services import check_breed_compatibility
            if not check_breed_compatibility(ram, ewe):
                return JsonResponse({
                    'success': False,
                    'message': f'Breed incompatibility: {ram.breed} ram cannot mate with {ewe.breed} ewe'
                })
            
            # Double-check inbreeding prevention
            from .services import check_for_inbreeding
            if not check_for_inbreeding(ewe, ram):
                relationships = get_family_relationship(ewe, ram)
                return JsonResponse({
                    'success': False,
                    'message': f'Breeding not allowed: {", ".join(relationships)}'
                })
            
            # Predict lamb breed
            lamb_breed, lamb_breed_level = predict_lamb_breed(ewe, ram)
            
            # Create breeding cycle
            breeding_cycle = BreedingCycle(
                ewe=ewe,
                ram=ram,
                start_date=start_date,
                created_by=request.user
            )
            breeding_cycle.save()
            
            # Add breed prediction to response
            breed_prediction_msg = ""
            if lamb_breed and lamb_breed_level:
                breed_prediction_msg = f" Predicted lamb: {lamb_breed} ({lamb_breed_level}%)"
            else:
                breed_prediction_msg = " Lamb breed requires manual assignment."
            
            return JsonResponse({
                'success': True,
                'message': f'Breeding cycle created successfully! Expected birth: {breeding_cycle.expected_birth_date}.{breed_prediction_msg}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def get_compatible_ewes_ajax(request, ram_id):
    """AJAX endpoint to get compatible ewes for selected ram"""
    try:
        ram = Sheep.objects.get(ear_tag_number=ram_id)
        compatible_ewes = get_compatible_ewes(ram)
        breed_compatibility_info = get_breed_compatibility_info(ram)
        
        ewes_data = []
        for ewe in compatible_ewes:
            # Predict lamb breed for each compatible ewe
            lamb_breed, lamb_breed_level = predict_lamb_breed(ewe, ram)
            
            ewes_data.append({
                'ear_tag_number': ewe.ear_tag_number,
                'breed': ewe.breed,
                'breed_level': ewe.breed_level,
                'type': ewe.type,
                'age_days': (timezone.now().date() - ewe.date_of_birth).days if ewe.date_of_birth else 'Unknown',
                'predicted_lamb_breed': lamb_breed,
                'predicted_lamb_level': lamb_breed_level
            })
        
        return JsonResponse({
            'success': True,
            'compatible_ewes': ewes_data,
            'total_compatible': len(compatible_ewes),
            'breed_compatibility_info': breed_compatibility_info
        })
    except Sheep.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Ram not found'
        })