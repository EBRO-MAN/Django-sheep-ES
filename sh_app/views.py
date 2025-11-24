# from django.shortcuts import render,redirect
from urllib import request
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
# from .models import Sheep
from .form import AddRecordForm
# from .services import get_available_rams, get_available_ewes, get_compatible_ewes
# from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime
from django.http import JsonResponse
from .models import Sheep, BreedingCycle, AuditLog
from .services import (get_available_rams, get_available_lambs,get_available_ewes, get_available_gimmers,get_available_young_rams, get_compatible_ewes, get_ram_capacity_info, 
                      get_family_relationship, distribute_ewes_by_priority, check_breed_compatibility, check_for_inbreeding,
                      predict_lamb_breed, get_breed_compatibility_info, )
import json

import logging

logger = logging.getLogger(__name__)


from django.views.generic import TemplateView, View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Avg
from datetime import timedelta
from datetime import date


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
    """Main breeding selection view"""
    rams = get_available_rams()
    ewes = get_available_ewes()
    lambs = get_available_lambs()
    young_rams = get_available_young_rams()
    gimmers = get_available_gimmers()
    
    selected_ram_id = request.GET.get('ram_id')
    selected_ram = None
    compatible_ewes = []
    
    if selected_ram_id:
        try:
            selected_ram = Sheep.objects.get(ear_tag_number=selected_ram_id)
            compatible_ewes = get_compatible_ewes(selected_ram)
        except Sheep.DoesNotExist:
            pass
    
    context = {
        'rams': rams,
        'ewes': ewes,
        'young_rams': young_rams,
        'gimmers': gimmers,
        'lambs': lambs,
        'selected_ram': selected_ram,
        'compatible_ewes': compatible_ewes,
    }
    
    return render(request, 'breeding.html', context)   
     
@login_required
def flash_rams_state(request):
    if request.method == "POST":
        selected = request.POST.getlist("rams")

        updated = Sheep.objects.filter(
            ear_tag_number__in=selected,
            state="SCILENT",
            type="RAM"
        ).update(state="FLASHING")

        messages.success(request, f"{updated} ram(s) set to FLASHING")
    return redirect('breeding_selection')

@login_required
def flash_ewes_state(request):
    if request.method == "POST":
        selected = request.POST.getlist("ewes")

        updated = Sheep.objects.filter(
            ear_tag_number__in=selected,
            state="SCILENT",
            type="EWE"
        ).update(state="FLASHING")

        messages.success(request, f"{updated} ewe(s) set to FLASHING")
    return redirect('breeding_selection')


@login_required
def breed_rams_state(request):
    if request.method == "POST":
        selected_rams = request.POST.getlist("rams")

        if not selected_rams:
            messages.warning(request, "No rams were selected.")
            return redirect('breeding_selection')

        # Update selected rams only if their current state is FLASHING
        updated = Sheep.objects.filter(
            ear_tag_number__in=selected_rams,
            state="FLASHING"
        ).update(state="BREEDING")

        if updated > 0:
            messages.success(request, f"{updated} ram(s) successfully set to BREEDING state.")
        else:
            messages.info(request, "No rams were updated. They may not be in FLASHING state.")

        return redirect('breeding_selection')

    return redirect('breeding_selection')


@login_required
def breed_sheep_state(request):
    if request.method == "POST":
        selected_sheep = request.POST.getlist("sheeps")

        if not selected_sheep:
            messages.warning(request, "No sheep were selected.")
            return redirect('breeding_selection')

        # Update selected rams only if their current state is FLASHING
        updated = Sheep.objects.filter(
            ear_tag_number__in=selected_sheep,
            state="FLASHING"
        ).update(state="BREEDING")

        if updated > 0:
            messages.success(request, f"{updated} sheep(s) successfully set to BREEDING state.")
        else:
            messages.info(request, "No sheep were updated. They may not be in FLASHING state.")

        return redirect('breeding_selection')

    return redirect('breeding_selection')

# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&


# class BreedingTaskView(View):
#     template_name = 'breeding_task.html'
    
#     def get(self, request):
#         # Get selected rams from session
#         selected_ram_ids = request.session.get('selected_rams', [])
        
#         print(f"DEBUG: Selected ram IDs from session: {selected_ram_ids}")
        
#         if not selected_ram_ids:
#             messages.warning(request, "Please select rams first")
#             return redirect('breeding_selection')
        
#         try:
#             # Validate rams exist
#             rams = Sheep.objects.filter(ear_tag_number__in=selected_ram_ids)
#             if len(rams) != len(selected_ram_ids):
#                 messages.error(request, "Some selected rams no longer exist")
#                 return redirect('breeding_selection')
            
#             print(f"DEBUG: Found {len(rams)} rams")
            
#             # Get ram objects with capacity info
#             for ram in rams:
#                 ram.capacity_info = get_ram_capacity_info(ram)
#                 print(f"DEBUG: Ram {ram.ear_tag_number} capacity: {ram.capacity_info}")
            
#             # Get ALL compatible ewes for all selected rams
#             all_compatible_ewes = set()
#             ram_compatible_ewes = {}
#             ram_compatible_ewes_by_ewe = {}  # Reverse mapping for template
            
#             for ram in rams:
#                 compatible_ewes = get_compatible_ewes(ram)
#                 ram_compatible_ewes[ram.ear_tag_number] = compatible_ewes
#                 all_compatible_ewes.update(compatible_ewes)
                
#                 # Build reverse mapping
#                 for ewe in compatible_ewes:
#                     if ewe.ear_tag_number not in ram_compatible_ewes_by_ewe:
#                         ram_compatible_ewes_by_ewe[ewe.ear_tag_number] = []
#                     ram_compatible_ewes_by_ewe[ewe.ear_tag_number].append(ram.ear_tag_number)
            
#             print(f"DEBUG: Found {len(all_compatible_ewes)} compatible ewes")
            
#             # Distribute ewes with breed priority and no duplicates
#             distributed_assignments = distribute_ewes_by_priority(rams, list(all_compatible_ewes))
#             print(f"DEBUG: Distributed assignments: {distributed_assignments}")
            
#             # Get unassigned ewes (incompatible + not assigned due to capacity/priority)
#             assigned_ewes = set()
#             for ewes in distributed_assignments.values():
#                 assigned_ewes.update([ewe.ear_tag_number for ewe in ewes])
            
#             unassigned_ewes = Sheep.objects.filter(
#                 sex='female',
#                 type__in=['ewe', 'gimmer'],
#                 is_healthy=True
#             ).exclude(ear_tag_number__in=assigned_ewes)
            
#             print(f"DEBUG: Found {len(unassigned_ewes)} unassigned ewes")
            
#             # Prepare JSON data for template
#             rams_json = self._prepare_rams_json(rams)
#             ewes_json = self._prepare_ewes_json(all_compatible_ewes, unassigned_ewes, ram_compatible_ewes_by_ewe)
#             initial_assignments = self._prepare_initial_assignments(distributed_assignments)
            
#             print(f"DEBUG: Rams JSON prepared: {len(rams_json)} rams")
#             print(f"DEBUG: Ewes JSON prepared: {len(ewes_json)} ewes")
            
#             context = {
#                 'rams': rams,
#                 'distributed_assignments': distributed_assignments,
#                 'unassigned_ewes': unassigned_ewes,
#                 'ram_compatible_ewes_by_ewe': ram_compatible_ewes_by_ewe,
#                 'initial_assignments_json': json.dumps(initial_assignments),
#                 'rams_json': json.dumps(rams_json),
#                 'ewes_json': json.dumps(ewes_json),
#             }
#             return render(request, self.template_name, context)
            
#         except Exception as e:
#             logger.error(f"Error in BreedingTaskView GET: {str(e)}")
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"Error loading breeding task: {str(e)}")
#             return redirect('breeding_selection')
    
#     def post(self, request):
#         """Handle form submission - redirect to breeding_info"""
#         print("DEBUG: BreedingTaskView POST received")
        
#         try:
#             breeding_assignments = json.loads(request.POST.get('breedingAssignments', '{}'))
#             print(f"DEBUG: Received breeding assignments: {breeding_assignments}")
#         except json.JSONDecodeError as e:
#             print(f"DEBUG: JSON decode error: {e}")
#             messages.error(request, "Invalid breeding assignments data")
#             return redirect('breeding_task')
        
#         if not breeding_assignments:
#             messages.error(request, "No breeding assignments provided")
#             return redirect('breeding_task')
        
#         # Validate no duplicate ewes
#         all_assigned_ewes = []
#         for ewe_list in breeding_assignments.values():
#             all_assigned_ewes.extend(ewe_list)
        
#         if len(all_assigned_ewes) != len(set(all_assigned_ewes)):
#             messages.error(request, "Error: Some ewes are assigned to multiple rams")
#             return redirect('breeding_task')
        
#         # Store in session
#         request.session['breeding_assignments'] = breeding_assignments
#         request.session.modified = True
        
#         print(f"DEBUG: Stored assignments in session, redirecting to breeding_info")
#         return redirect('breeding_info')
    
#     def _prepare_rams_json(self, rams):
#         """Prepare rams data for JSON serialization"""
#         rams_data = []
#         for ram in rams:
#             rams_data.append({
#                 'ear_tag': ram.ear_tag_number,
#                 'breed': ram.breed,
#                 'type': ram.type,
#                 'remaining': ram.capacity_info['remaining'],
#                 'capacity': ram.capacity_info['max'],
#                 'current': ram.capacity_info['current']
#             })
#         return rams_data
    
#     def _prepare_ewes_json(self, compatible_ewes, unassigned_ewes, ram_compatible_ewes_by_ewe):
#         """Prepare ewes data for JSON serialization"""
#         ewes_data = {}
        
#         # Add compatible ewes
#         for ewe in compatible_ewes:
#             ewes_data[ewe.ear_tag_number] = {
#                 'ear_tag': ewe.ear_tag_number,
#                 'breed': ewe.breed,
#                 'type': ewe.type,
#                 'compatible_with': ram_compatible_ewes_by_ewe.get(ewe.ear_tag_number, [])
#             }
        
#         # Add unassigned ewes
#         for ewe in unassigned_ewes:
#             ewes_data[ewe.ear_tag_number] = {
#                 'ear_tag': ewe.ear_tag_number,
#                 'breed': ewe.breed,
#                 'type': ewe.type,
#                 'compatible_with': ram_compatible_ewes_by_ewe.get(ewe.ear_tag_number, [])
#             }
        
#         return ewes_data
    
#     def _prepare_initial_assignments(self, distributed_assignments):
#         """Prepare initial assignments for JSON serialization"""
#         initial_assignments = {}
#         for ram_id, ewes in distributed_assignments.items():
#             initial_assignments[ram_id] = [ewe.ear_tag_number for ewe in ewes]
#         return initial_assignments

# views.py

from django.views.decorators.http import require_POST
# ... existing imports ...

# 1. NEW VIEW: Handle the initial Ram selection from breeding.html
@login_required
@require_POST
def process_ram_selection(request):
    """
    Receives the list of selected rams from breeding.html,
    stores them in the session, and redirects to the task page.
    """
    selected_ram_ids = request.POST.getlist('rams')
    
    if not selected_ram_ids:
        messages.warning(request, "Please select at least one ram to proceed.")
        return redirect('breeding_selection')

    # Validate that these rams actually exist and are in the correct state
    valid_rams = Sheep.objects.filter(
        ear_tag_number__in=selected_ram_ids,
        type='RAM'  # Optional: Add state='FLASHING' check if strict
    ).values_list('ear_tag_number', flat=True)

    if not valid_rams:
        messages.error(request, "Invalid rams selected.")
        return redirect('breeding_selection')

    # Store in session
    request.session['selected_rams'] = list(valid_rams)
    request.session.modified = True

    return redirect('breeding_task')


# 2. UPDATED VIEW: The main Breeding Task logic
class BreedingTaskView(View):
    template_name = 'breeding_task.html'
    
    def get(self, request):
        # 1. Retrieve selected rams from session
        selected_ram_ids = request.session.get('selected_rams', [])
        
        if not selected_ram_ids:
            messages.warning(request, "Session expired or no rams selected. Please select rams again.")
            return redirect('breeding_selection')
        
        try:
            # 2. Fetch Ram Objects
            rams = Sheep.objects.filter(ear_tag_number__in=selected_ram_ids)
            
            # 3. Get Capacity Info & Compatible Ewes
            all_compatible_ewes = set()
            ram_compatible_ewes_by_ewe = {}  # Map: ewe_id -> [ram_id1, ram_id2]
            
            for ram in rams:
                ram.capacity_info = get_ram_capacity_info(ram) # Ensure this service function exists
                
                # Get compatible ewes for this specific ram
                comp_ewes = get_compatible_ewes(ram) # Ensure this service function exists
                
                for ewe in comp_ewes:
                    all_compatible_ewes.add(ewe)
                    
                    if ewe.ear_tag_number not in ram_compatible_ewes_by_ewe:
                        ram_compatible_ewes_by_ewe[ewe.ear_tag_number] = []
                    ram_compatible_ewes_by_ewe[ewe.ear_tag_number].append(ram.ear_tag_number)

            # 4. Distribute Ewes (Initial Assignment)
            # Convert set to list for distribution function
            distributed_assignments = distribute_ewes_by_priority(rams, list(all_compatible_ewes))
            
            # 5. Identify Unassigned Ewes
            # Get IDs of currently assigned ewes
            assigned_ewe_ids = set()
            for ewe_list in distributed_assignments.values():
                for ewe in ewe_list:
                    assigned_ewe_ids.add(ewe.ear_tag_number)
            
            # Filter unassigned from the compatible list AND get completely unassigned ones from DB
            # (depending on if you want to show ALL ewes or just compatible ones)
            # Here we show all available ewes that aren't assigned yet
            unassigned_ewes = Sheep.objects.filter(
                sex='FEMALE',
                type__in=['EWE'],
                is_healthy=True
            ).exclude(ear_tag_number__in=assigned_ewe_ids)

            # 6. Prepare JSON Data for JavaScript
            rams_json = [
                {
                    'ear_tag': ram.ear_tag_number,
                    'breed': ram.breed,
                    'remaining': ram.capacity_info.get('remaining', 0),
                    'capacity': ram.capacity_info.get('max', 0)
                } for ram in rams
            ]
            
            ewes_json = {}
            # Combine compatible and unassigned for the JS lookup
            all_relevant_ewes = list(all_compatible_ewes) + list(unassigned_ewes)
            for ewe in all_relevant_ewes:
                ewes_json[ewe.ear_tag_number] = {
                    'ear_tag': ewe.ear_tag_number,
                    'breed': ewe.breed,
                    'type': ewe.type,
                    'compatible_with': ram_compatible_ewes_by_ewe.get(ewe.ear_tag_number, [])
                }

            initial_assignments_simple = {
                ram_id: [ewe.ear_tag_number for ewe in ewes]
                for ram_id, ewes in distributed_assignments.items()
            }

            context = {
                'rams': rams,
                'distributed_assignments': distributed_assignments,
                'unassigned_ewes': unassigned_ewes,
                'ram_compatible_ewes_by_ewe': ram_compatible_ewes_by_ewe,
                'rams_json': json.dumps(rams_json),
                'ewes_json': json.dumps(ewes_json),
                'initial_assignments_json': json.dumps(initial_assignments_simple),
            }
            return render(request, self.template_name, context)

        except Exception as e:
            logger.error(f"Error in BreedingTaskView: {e}")
            messages.error(request, f"System Error: {e}")
            return redirect('breeding_selection')

    def post(self, request):
        """
        Handles the Save button from the Task page.
        Redirects to the Info/Confirmation page.
        """
        try:
            assignments_json = request.POST.get('breedingAssignments')
            if not assignments_json:
                raise ValueError("No assignment data received.")
            
            assignments = json.loads(assignments_json)
            
            # Store finalized assignments in session
            request.session['breeding_assignments'] = assignments
            request.session.modified = True
            
            return redirect('breeding_info')
            
        except Exception as e:
            messages.error(request, f"Error saving assignments: {e}")
            return redirect('breeding_task')

class BreedingInfoView(View):
    template_name = 'breeding_info.html'
    
    def get(self, request):
        # Get final assignments from session (for confirmation after POST)
        breeding_assignments = request.session.get('breeding_assignments', {})
        
        if not breeding_assignments:
            messages.warning(request, "No breeding assignments found")
            return redirect('breeding_task')
        
        # Prepare breeding information for display
        breeding_info = self._prepare_breeding_info(breeding_assignments)
        
        context = {
            'breeding_info': breeding_info
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle final breeding plan creation"""
        try:
            # Get assignments from POST data, not session
            breeding_assignments_json = request.POST.get('breedingAssignments', '{}')
            breeding_assignments = json.loads(breeding_assignments_json)
            
            logger.info(f"Received breeding assignments: {breeding_assignments}")
            
            if not breeding_assignments:
                messages.error(request, "No breeding assignments provided")
                return redirect('breeding_task')
            
            # Store in session for confirmation page
            request.session['breeding_assignments'] = breeding_assignments
            
            # Create breeding cycles
            created_count = self._create_breeding_cycles(breeding_assignments)
            
            if created_count > 0:
                messages.success(request, f"Successfully created {created_count} breeding cycles")
            else:
                messages.warning(request, "No breeding cycles were created")
                
            return redirect('breeding_info')
            
        except json.JSONDecodeError as e:
            messages.error(request, f"Invalid data format: {str(e)}")
            return redirect('breeding_task')
        except Exception as e:
            logger.error(f"Error creating breeding cycles: {str(e)}")
            messages.error(request, f"Error creating breeding cycles: {str(e)}")
            return redirect('breeding_task')
    
    def _prepare_breeding_info(self, breeding_assignments):
        """Prepare breeding information for display"""
        breeding_info = []
        for ram_id, ewe_ids in breeding_assignments.items():
            try:
                ram = Sheep.objects.get(ear_tag_number=ram_id)
                ewes = Sheep.objects.filter(ear_tag_number__in=ewe_ids)
                
                for ewe in ewes:
                    breeding_info.append({
                        'ram': ram,
                        'ewe': ewe,
                        'start_date': date.today(),
                        'expected_birth_date': date.today() + timedelta(days=155),
                        'capacity_info': get_ram_capacity_info(ram)
                    })
            except Sheep.DoesNotExist as e:
                logger.warning(f"Sheep not found: {e}")
                continue
        
        return breeding_info
    
    def _create_breeding_cycles(self, breeding_assignments):
        """Create breeding cycles in database"""
        created_count = 0
        for ram_id, ewe_ids in breeding_assignments.items():
            try:
                ram = Sheep.objects.get(ear_tag_number=ram_id)
                for ewe_id in ewe_ids:
                    try:
                        ewe = Sheep.objects.get(ear_tag_number=ewe_id)
                        
                        # Check if breeding cycle already exists to avoid duplicates
                        existing_cycle = BreedingCycle.objects.filter(
                            ewe=ewe, 
                            ram=ram, 
                            start_date=date.today()
                        ).first()
                        
                        if existing_cycle:
                            logger.info(f"Breeding cycle already exists for {ewe_id} and {ram_id}")
                            continue
                        
                        # Create breeding cycle
                        breeding_cycle = BreedingCycle.objects.create(
                            cycle_id=f"BC_{ram_id}_{ewe_id}_{date.today().strftime('%Y%m%d')}",
                            ewe=ewe,
                            ram=ram,
                            start_date=date.today(),
                            status='planned'
                        )
                        created_count += 1
                        logger.info(f"Created breeding cycle: {breeding_cycle.cycle_id}")
                        
                    except Sheep.DoesNotExist:
                        logger.warning(f"Ewe not found: {ewe_id}")
                        continue
            except Sheep.DoesNotExist:
                logger.warning(f"Ram not found: {ram_id}")
                continue
        
        return created_count

@login_required
def debug_breeding_flow(request):
    """Debug view to test the entire breeding flow"""
    if request.method == 'POST':
        # Simulate selecting some rams
        test_rams = Sheep.objects.filter(sex='male', type__in=['ram'], is_healthy=True)[:2]
        if test_rams:
            request.session['selected_rams'] = [ram.ear_tag_number for ram in test_rams]
            request.session.modified = True
            messages.success(request, f"Auto-selected {len(test_rams)} rams for testing")
            return redirect('breeding_task')
        else:
            messages.error(request, "No rams available for testing")
    
    return render(request, 'debug_breeding.html')

@login_required
def create_breeding_cycle(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            breeding_cycles = data.get('breeding_cycles', [])
            created_cycles = []

            for cycle_data in breeding_cycles:
                ewe_id = cycle_data.get('ewe_id')
                ram_id = cycle_data.get('ram_id')
                start_date_str = cycle_data.get('start_date')

                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                ewe = Sheep.objects.get(ear_tag_number=ewe_id)
                ram = Sheep.objects.get(ear_tag_number=ram_id)

                breeding_cycle = BreedingCycle(
                    ewe=ewe,
                    ram=ram,
                    start_date=start_date,
                    created_by=request.user
                )
                breeding_cycle.save()
                created_cycles.append(breeding_cycle.cycle_id)

            return JsonResponse({
                'success': True,
                'message': f'Successfully created {len(created_cycles)} breeding cycles',
                'cycle_ids': created_cycles
            })

        except Exception as e:
            logger.error(f"Error creating breeding cycle: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})

    # &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&   
# @login_required
# def breeding_task(request):
#     template_name = 'breeding_task.html'
    
#     def get(self, request):
#         # Get selected rams from session with debug
#         selected_ram_ids = request.session.get('selected_rams', [])
#         print(f"DEBUG BreedingTaskView GET - Session keys: {list(request.session.keys())}")
#         print(f"DEBUG BreedingTaskView GET - Selected rams from session: {selected_ram_ids}")
        
#         if not selected_ram_ids:
#             messages.warning(request, "Please select rams first")
#             return redirect('breeding_selection')
        
#         try:
#             # Get ram objects
#             rams = Sheep.objects.filter(ear_tag_number__in=selected_ram_ids)
#             if not rams.exists():
#                 messages.error(request, "Selected rams not found in database")
#                 return redirect('breeding_selection')
                
#             # Add capacity info
#             for ram in rams:
#                 ram.capacity_info = get_ram_capacity_info(ram)
            
#             # Get compatible ewes
#             all_compatible_ewes = set()
#             for ram in rams:
#                 compatible_ewes = get_compatible_ewes(ram)
#                 all_compatible_ewes.update(compatible_ewes)
            
#             # Distribute ewes
#             distributed_assignments = self.distribute_ewes_equally(rams, list(all_compatible_ewes))
            
#             # Get unassigned ewes
#             unassigned_ewes = Sheep.objects.filter(
#                 sex='female',
#                 type__in=['ewe', 'gimmer'],
#                 is_healthy=True
#             ).exclude(ear_tag_number__in=[ewe.ear_tag_number for ewe in all_compatible_ewes])
            
#             # Prepare JSON data
#             import json
#             initial_assignments_dict = {}
#             for ram_ear, ewes in distributed_assignments.items():
#                 initial_assignments_dict[ram_ear] = [
#                     {"ear_tag": ewe.ear_tag_number, "breed": ewe.breed} 
#                     for ewe in ewes
#                 ]
            
#             context = {
#                 'rams': rams,
#                 'distributed_assignments': distributed_assignments,
#                 'unassigned_ewes': unassigned_ewes,
#                 'initial_assignments_json': json.dumps(initial_assignments_dict),
#             }
            
#             print(f"DEBUG - Context prepared with {len(rams)} rams and {len(unassigned_ewes)} unassigned ewes")
#             return render(request, self.template_name, context)
            
#         except Exception as e:
#             print(f"ERROR in BreedingTaskView GET: {str(e)}")
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"Error loading breeding task: {str(e)}")
#             return redirect('breeding_selection')
    
#     def post(self, request):
#         """Handle form submission"""
#         print(f"DEBUG BreedingTaskView POST - Session keys: {list(request.session.keys())}")
#         print(f"DEBUG BreedingTaskView POST - Selected rams in session: {request.session.get('selected_rams')}")
        
#         # Get breeding assignments from form
#         breeding_assignments_json = request.POST.get('breedingAssignments', '{}')
#         print(f"DEBUG - Received breedingAssignments: {breeding_assignments_json}")
        
#         try:
#             breeding_assignments = json.loads(breeding_assignments_json)
#         except json.JSONDecodeError as e:
#             print(f"ERROR - JSON decode error: {e}")
#             messages.error(request, "Invalid breeding assignments data")
#             return redirect('breeding_task')
        
#         if not breeding_assignments:
#             messages.error(request, "No breeding assignments provided")
#             return redirect('breeding_task')
        
#         # Validate we have assignments
#         total_assignments = sum(len(ewes) for ewes in breeding_assignments.values())
#         if total_assignments == 0:
#             messages.error(request, "Please assign at least one ewe before proceeding")
#             return redirect('breeding_task')
        
#         # Store in session
#         request.session['breeding_assignments'] = breeding_assignments
#         request.session.modified = True
        
#         print(f"DEBUG - Stored breeding assignments in session: {request.session.get('breeding_assignments')}")
#         return redirect('breeding_info')
    
#     def distribute_ewes_equally(self, rams, all_compatible_ewes):
#         """Distribute ewes equally among available rams"""
#         if not rams or not all_compatible_ewes:
#             return {}
        
#         assignments = {}
#         for ram in rams:
#             assignments[ram.ear_tag_number] = []
        
#         # Simple round-robin distribution
#         for i, ewe in enumerate(all_compatible_ewes):
#             ram_index = i % len(rams)
#             ram_id = rams[ram_index].ear_tag_number
#             assignments[ram_id].append(ewe)
        
#         return assignments


# *********************************************************************************************************
# class BreedingTaskView(View):
#     template_name = 'breeding_task.html'
    
#     def get(self, request):
#         # Get selected rams from session
#         selected_ram_ids = request.session.get('selected_rams', [])
        
#         if not selected_ram_ids:
#             messages.warning(request, "Please select rams first")
#             return redirect('breeding_selection')
        
#         try:
#             # Get ram objects with capacity info
#             rams = Sheep.objects.filter(ear_tag_number__in=selected_ram_ids)
#             for ram in rams:
#                 ram.capacity_info = get_ram_capacity_info(ram)
            
#             # Get ALL compatible ewes for all selected rams
#             all_compatible_ewes = set()
#             ram_compatible_ewes = {}
            
#             for ram in rams:
#                 compatible_ewes = get_compatible_ewes(ram)
#                 ram_compatible_ewes[ram.ear_tag_number] = compatible_ewes
#                 all_compatible_ewes.update(compatible_ewes)
            
#             # Distribute ewes with breed priority and no duplicates
#             distributed_assignments = distribute_ewes_by_priority(rams, list(all_compatible_ewes))
            
#             # Get unassigned ewes (incompatible + not assigned due to capacity/priority)
#             assigned_ewes = set()
#             for ewes in distributed_assignments.values():
#                 assigned_ewes.update([ewe.ear_tag_number for ewe in ewes])
            
#             unassigned_ewes = Sheep.objects.filter(
#                 sex='female',
#                 type__in=['ewe', 'gimmer'],
#                 is_healthy=True
#             ).exclude(ear_tag_number__in=assigned_ewes)
            
#             # Prepare initial assignments for template
#             import json
#             initial_assignments = {}
#             for ram_id, ewes in distributed_assignments.items():
#                 initial_assignments[ram_id] = [ewe.ear_tag_number for ewe in ewes]
            
#             context = {
#                 'rams': rams,
#                 'distributed_assignments': distributed_assignments,
#                 'unassigned_ewes': unassigned_ewes,
#                 'ram_compatible_ewes': ram_compatible_ewes,
#                 'initial_assignments_json': json.dumps(initial_assignments),
#             }
#             return render(request, self.template_name, context)
            
#         except Exception as e:
#             print(f"Error in BreedingTaskView: {e}")
#             messages.error(request, f"Error loading breeding task: {str(e)}")
#             return redirect('breeding_selection')
    
#     def post(self, request):
#         """Handle form submission"""
#         try:
#             breeding_assignments = json.loads(request.POST.get('breedingAssignments', '{}'))
#         except json.JSONDecodeError:
#             messages.error(request, "Invalid breeding assignments data")
#             return redirect('breeding_task')
        
#         if not breeding_assignments:
#             messages.error(request, "No breeding assignments provided")
#             return redirect('breeding_task')
        
#         # Validate no duplicate ewes
#         all_assigned_ewes = []
#         for ewe_list in breeding_assignments.values():
#             all_assigned_ewes.extend(ewe_list)
        
#         if len(all_assigned_ewes) != len(set(all_assigned_ewes)):
#             messages.error(request, "Error: Some ewes are assigned to multiple rams")
#             return redirect('breeding_task')
        
#         # Store in session
#         request.session['breeding_assignments'] = breeding_assignments
#         request.session.modified = True
        
#         return redirect('breeding_info')

# ******************************************************************************************************************
    
# def breeding_task(request):
#     # Get unassigned ewes
#     unassigned_ewes = Sheep.objects.filter(
#         sex='female',
#         breeding_assignment__isnull=True,
#         state__in=["SILENT", "FLASHING"]  # or whatever states are appropriate
#     )
    
#     context = {
#         'ewes': unassigned_ewes,
#         'rams': Sheep.objects.filter(state="FLASHING"),  # or appropriate filter
#         # ... other context variables
#     }
#     return render(request, 'breeding/breeding_task.html', context)
# //////////////////////////////////
    

# class BreedingInfoView(View):
#     template_name = 'breeding_info.html'
    
#     def get(self, request):
#         # Get final assignments from session
#         breeding_assignments = request.session.get('breeding_assignments', {})
        
#         if not breeding_assignments:
#             messages.warning(request, "No breeding assignments found")
#             return redirect('breeding_task')
        
#         # Prepare breeding information for display
#         breeding_info = []
#         for ram_id, ewe_ids in breeding_assignments.items():
#             try:
#                 ram = Sheep.objects.get(ear_tag_number=ram_id)
#                 ewes = Sheep.objects.filter(ear_tag_number__in=ewe_ids)
                
#                 for ewe in ewes:
#                     breeding_info.append({
#                         'ram': ram,
#                         'ewe': ewe,
#                         'start_date': date.today(),
#                         'expected_birth_date': date.today() + timedelta(days=155),
#                         'capacity_info': get_ram_capacity_info(ram)
#                     })
#             except Sheep.DoesNotExist:
#                 continue
        
#         context = {
#             'breeding_info': breeding_info
#         }
#         return render(request, self.template_name, context)
    
#     def post(self, request):
#         """Handle final breeding plan creation"""
#         breeding_assignments = json.loads(request.POST.get('breeding_assignments', '{}'))
        
#         if not breeding_assignments:
#             messages.error(request, "No breeding assignments provided")
#             return redirect('breeding_task')
        
#         # Store in session for confirmation page
#         request.session['breeding_assignments'] = breeding_assignments
        
#         # Create breeding cycles
#         created_count = 0
#         for ram_id, ewe_ids in breeding_assignments.items():
#             try:
#                 ram = Sheep.objects.get(ear_tag_number=ram_id)
#                 for ewe_id in ewe_ids:
#                     try:
#                         ewe = Sheep.objects.get(ear_tag_number=ewe_id)
                        
#                         # Create breeding cycle
#                         breeding_cycle = BreedingCycle.objects.create(
#                             cycle_id=f"BC_{ram_id}_{ewe_id}_{date.today().strftime('%Y%m%d')}",
#                             ewe=ewe,
#                             ram=ram,
#                             start_date=date.today(),
#                             status='planned'
#                         )
#                         created_count += 1
#                     except Sheep.DoesNotExist:
#                         continue
#             except Sheep.DoesNotExist:
#                 continue
        
#         messages.success(request, f"Successfully created {created_count} breeding cycles")
#         return redirect('breeding_info')    

# **************************************************************************************************************************************************
# class BreedingInfoView(View):
#     template_name = 'breeding_info.html'
    
#     def get(self, request):
#         # Get final assignments from session (for confirmation after POST)
#         breeding_assignments = request.session.get('breeding_assignments', {})
        
#         if not breeding_assignments:
#             messages.warning(request, "No breeding assignments found")
#             return redirect('breeding_task')
        
#         # Prepare breeding information for display
#         breeding_info = self._prepare_breeding_info(breeding_assignments)
        
#         context = {
#             'breeding_info': breeding_info
#         }
#         return render(request, self.template_name, context)
    
#     def post(self, request):
#         """Handle final breeding plan creation"""
#         try:
#             # Get assignments from POST data, not session
#             breeding_assignments_json = request.POST.get('breedingAssignments', '{}')
#             breeding_assignments = json.loads(breeding_assignments_json)
            
#             print(f"Received breeding assignments: {breeding_assignments}")  # Debug
            
#             if not breeding_assignments:
#                 messages.error(request, "No breeding assignments provided")
#                 return redirect('breeding_task')
            
#             # Store in session for confirmation page
#             request.session['breeding_assignments'] = breeding_assignments
            
#             # Create breeding cycles
#             created_count = self._create_breeding_cycles(breeding_assignments)
            
#             if created_count > 0:
#                 messages.success(request, f"Successfully created {created_count} breeding cycles")
#             else:
#                 messages.warning(request, "No breeding cycles were created")
                
#             return redirect('breeding_info')
            
#         except json.JSONDecodeError as e:
#             messages.error(request, f"Invalid data format: {str(e)}")
#             return redirect('breeding_task')
#         except Exception as e:
#             messages.error(request, f"Error creating breeding cycles: {str(e)}")
#             return redirect('breeding_task')
    
#     def _prepare_breeding_info(self, breeding_assignments):
#         """Prepare breeding information for display"""
#         breeding_info = []
#         for ram_id, ewe_ids in breeding_assignments.items():
#             try:
#                 ram = Sheep.objects.get(ear_tag_number=ram_id)
#                 ewes = Sheep.objects.filter(ear_tag_number__in=ewe_ids)
                
#                 for ewe in ewes:
#                     breeding_info.append({
#                         'ram': ram,
#                         'ewe': ewe,
#                         'start_date': date.today(),
#                         'expected_birth_date': date.today() + timedelta(days=155),
#                         'capacity_info': get_ram_capacity_info(ram)
#                     })
#             except Sheep.DoesNotExist as e:
#                 print(f"Sheep not found: {e}")  # Debug
#                 continue
        
#         return breeding_info
    
#     def _create_breeding_cycles(self, breeding_assignments):
#         """Create breeding cycles in database"""
#         created_count = 0
#         for ram_id, ewe_ids in breeding_assignments.items():
#             try:
#                 ram = Sheep.objects.get(ear_tag_number=ram_id)
#                 for ewe_id in ewe_ids:
#                     try:
#                         ewe = Sheep.objects.get(ear_tag_number=ewe_id)
                        
#                         # Check if breeding cycle already exists to avoid duplicates
#                         existing_cycle = BreedingCycle.objects.filter(
#                             ewe=ewe, 
#                             ram=ram, 
#                             start_date=date.today()
#                         ).first()
                        
#                         if existing_cycle:
#                             print(f"Breeding cycle already exists for {ewe_id} and {ram_id}")
#                             continue
                        
#                         # Create breeding cycle
#                         breeding_cycle = BreedingCycle.objects.create(
#                             cycle_id=f"BC_{ram_id}_{ewe_id}_{date.today().strftime('%Y%m%d')}",
#                             ewe=ewe,
#                             ram=ram,
#                             start_date=date.today(),
#                             status='planned'
#                         )
#                         created_count += 1
#                         print(f"Created breeding cycle: {breeding_cycle.cycle_id}")  # Debug
                        
#                     except Sheep.DoesNotExist:
#                         print(f"Ewe not found: {ewe_id}")
#                         continue
#             except Sheep.DoesNotExist:
#                 print(f"Ram not found: {ram_id}")
#                 continue
        
#         return created_count

# *****************************************************************************************
# # sh_app/views.py
# from django.shortcuts import render, redirect
# from django.views.generic import TemplateView, View
# from django.contrib import messages
# from django.http import JsonResponse
# import json
# from datetime import date, timedelta
# from .models import Sheep, BreedingCycle
# from .services import get_available_rams, get_compatible_ewes, get_ram_capacity_info

# # sh_app/views.py
# class BreedingHomeView(TemplateView):
#     template_name = 'sh_app/breeding_home.html'
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['sheep_list'] = Sheep.objects.all()
        
#         # Add capacity info to rams
#         rams = get_available_rams()
#         for ram in rams:
#             ram.capacity_info = get_ram_capacity_info(ram)
#         context['rams'] = rams
        
#         print(f"DEBUG - Session keys in GET: {list(self.request.session.keys())}")
#         print(f"DEBUG - Selected rams in session: {self.request.session.get('selected_rams', 'NOT FOUND')}")
        
#         return context
    
#     def post(self, request):
#         """Handle ram selection from modal"""
#         selected_rams = request.POST.getlist('rams')
#         print(f"DEBUG BreedingHomeView POST - Selected rams: {selected_rams}")
#         print(f"DEBUG - All POST data: {dict(request.POST)}")
        
#         if not selected_rams:
#             messages.error(request, "Please select at least one ram")
#             return redirect('breeding_home')
        
#         # Store selected rams in session
#         request.session['selected_rams'] = selected_rams
#         request.session.modified = True
#         print(f"DEBUG - Session after setting: {request.session.get('selected_rams')}")
#         print(f"DEBUG - All session data: {dict(request.session)}")
        
#         return redirect('breeding_task')
    
# # sh_app/views.py
# from django.shortcuts import render, redirect
# from django.views.generic import TemplateView, View
# from django.contrib import messages
# import json
# from datetime import date, timedelta
# from .models import Sheep, BreedingCycle
# from .services import get_available_rams, get_compatible_ewes, get_ram_capacity_info

# # sh_app/views.py
# class BreedingTaskView(View):
#     template_name = 'sh_app/breeding_task.html'
    
#     def get(self, request):
#         # Get selected rams from session with debug
#         selected_ram_ids = request.session.get('selected_rams', [])
#         print(f"DEBUG BreedingTaskView GET - Session keys: {list(request.session.keys())}")
#         print(f"DEBUG BreedingTaskView GET - Selected rams from session: {selected_ram_ids}")
        
#         if not selected_ram_ids:
#             messages.warning(request, "Please select rams first")
#             return redirect('breeding_home')
        
#         try:
#             # Get ram objects
#             rams = Sheep.objects.filter(ear_tag_number__in=selected_ram_ids)
#             if not rams.exists():
#                 messages.error(request, "Selected rams not found in database")
#                 return redirect('breeding_home')
                
#             # Add capacity info
#             for ram in rams:
#                 ram.capacity_info = get_ram_capacity_info(ram)
            
#             # Get compatible ewes
#             all_compatible_ewes = set()
#             for ram in rams:
#                 compatible_ewes = get_compatible_ewes(ram)
#                 all_compatible_ewes.update(compatible_ewes)
            
#             # Distribute ewes
#             distributed_assignments = self.distribute_ewes_equally(rams, list(all_compatible_ewes))
            
#             # Get unassigned ewes
#             unassigned_ewes = Sheep.objects.filter(
#                 sex='female',
#                 type__in=['ewe', 'gimmer'],
#                 is_healthy=True
#             ).exclude(ear_tag_number__in=[ewe.ear_tag_number for ewe in all_compatible_ewes])
            
#             # Prepare JSON data
#             import json
#             initial_assignments_dict = {}
#             for ram_ear, ewes in distributed_assignments.items():
#                 initial_assignments_dict[ram_ear] = [
#                     {"ear_tag": ewe.ear_tag_number, "breed": ewe.breed} 
#                     for ewe in ewes
#                 ]
            
#             context = {
#                 'rams': rams,
#                 'distributed_assignments': distributed_assignments,
#                 'unassigned_ewes': unassigned_ewes,
#                 'initial_assignments_json': json.dumps(initial_assignments_dict),
#             }
            
#             print(f"DEBUG - Context prepared with {len(rams)} rams and {len(unassigned_ewes)} unassigned ewes")
#             return render(request, self.template_name, context)
            
#         except Exception as e:
#             print(f"ERROR in BreedingTaskView GET: {str(e)}")
#             import traceback
#             traceback.print_exc()
#             messages.error(request, f"Error loading breeding task: {str(e)}")
#             return redirect('breeding_home')
    
#     def post(self, request):
#         """Handle form submission"""
#         print(f"DEBUG BreedingTaskView POST - Session keys: {list(request.session.keys())}")
#         print(f"DEBUG BreedingTaskView POST - Selected rams in session: {request.session.get('selected_rams')}")
        
#         # Get breeding assignments from form
#         breeding_assignments_json = request.POST.get('breedingAssignments', '{}')
#         print(f"DEBUG - Received breedingAssignments: {breeding_assignments_json}")
        
#         try:
#             breeding_assignments = json.loads(breeding_assignments_json)
#         except json.JSONDecodeError as e:
#             print(f"ERROR - JSON decode error: {e}")
#             messages.error(request, "Invalid breeding assignments data")
#             return redirect('breeding_task')
        
#         if not breeding_assignments:
#             messages.error(request, "No breeding assignments provided")
#             return redirect('breeding_task')
        
#         # Validate we have assignments
#         total_assignments = sum(len(ewes) for ewes in breeding_assignments.values())
#         if total_assignments == 0:
#             messages.error(request, "Please assign at least one ewe before proceeding")
#             return redirect('breeding_task')
        
#         # Store in session
#         request.session['breeding_assignments'] = breeding_assignments
#         request.session.modified = True
        
#         print(f"DEBUG - Stored breeding assignments in session: {request.session.get('breeding_assignments')}")
#         return redirect('breeding_info')
    
#     def distribute_ewes_equally(self, rams, all_compatible_ewes):
#         """Distribute ewes equally among available rams"""
#         if not rams or not all_compatible_ewes:
#             return {}
        
#         assignments = {}
#         for ram in rams:
#             assignments[ram.ear_tag_number] = []
        
#         # Simple round-robin distribution
#         for i, ewe in enumerate(all_compatible_ewes):
#             ram_index = i % len(rams)
#             ram_id = rams[ram_index].ear_tag_number
#             assignments[ram_id].append(ewe)
        
#         return assignments

# class BreedingInfoView(View):
#     template_name = 'sh_app/breeding_info.html'
    
#     def get(self, request):
#         # Get final assignments from session
#         breeding_assignments = request.session.get('breeding_assignments', {})
        
#         if not breeding_assignments:
#             messages.warning(request, "No breeding assignments found")
#             return redirect('breeding_task')
        
#         # Prepare breeding information for display
#         breeding_info = []
#         for ram_id, ewe_ids in breeding_assignments.items():
#             try:
#                 ram = Sheep.objects.get(ear_tag_number=ram_id)
#                 ewes = Sheep.objects.filter(ear_tag_number__in=ewe_ids)
                
#                 for ewe in ewes:
#                     breeding_info.append({
#                         'ram': ram,
#                         'ewe': ewe,
#                         'start_date': date.today(),
#                         'expected_birth_date': date.today() + timedelta(days=155),
#                         'capacity_info': get_ram_capacity_info(ram)
#                     })
#             except Sheep.DoesNotExist:
#                 continue
        
#         context = {
#             'breeding_info': breeding_info
#         }
#         return render(request, self.template_name, context)
    
#     def post(self, request):
#         """Handle final breeding plan creation"""
#         breeding_assignments = json.loads(request.POST.get('breeding_assignments', '{}'))
        
#         if not breeding_assignments:
#             messages.error(request, "No breeding assignments provided")
#             return redirect('breeding_task')
        
#         # Validate no duplicate ewes
#         all_assigned_ewes = []
#         for ewe_list in breeding_assignments.values():
#             all_assigned_ewes.extend(ewe_list)
        
#         if len(all_assigned_ewes) != len(set(all_assigned_ewes)):
#             messages.error(request, "Error: Some ewes are assigned to multiple rams")
#             return redirect('breeding_task')
        
#         # Store in session for confirmation page
#         request.session['breeding_assignments'] = breeding_assignments
        
#         # Create breeding cycles
#         created_count = 0
#         for ram_id, ewe_ids in breeding_assignments.items():
#             try:
#                 ram = Sheep.objects.get(ear_tag_number=ram_id)
#                 for ewe_id in ewe_ids:
#                     try:
#                         ewe = Sheep.objects.get(ear_tag_number=ewe_id)
                        
#                         # Create breeding cycle
#                         breeding_cycle = BreedingCycle.objects.create(
#                             cycle_id=f"BC_{ram_id}_{ewe_id}_{date.today().strftime('%Y%m%d')}",
#                             ewe=ewe,
#                             ram=ram,
#                             start_date=date.today(),
#                             status='planned'
#                         )
#                         created_count += 1
#                     except Sheep.DoesNotExist:
#                         continue
#             except Sheep.DoesNotExist:
#                 continue
        
#         messages.success(request, f"Successfully created {created_count} breeding cycles")
#         return redirect('breeding_info')




    
# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from django.http import JsonResponse
# from django.utils import timezone
# from .models import Sheep, BreedingCycle
# from .services import get_available_rams, get_available_ewes, get_compatible_ewes, check_breed_compatibility
# import json

# @login_required
# def breeding_home(request):
#     """Main breeding page showing all available sheep"""
#     rams = get_available_rams()
#     ewes = get_available_ewes()
    
#     context = {
#         'rams': rams,
#         'ewes': ewes,
#         'total_sheep': len(rams) + len(ewes),
#     }
#     return render(request, 'breeding/breeding_home.html', context)

# @login_required
# def breeding_task(request):
#     """Breeding task page with selected rams and compatible ewes"""
#     selected_ram_ids = request.GET.getlist('selected_rams')
    
#     if not selected_ram_ids:
#         messages.error(request, "No rams selected for breeding")
#         return redirect('breeding_home')
    
#     selected_rams = []
#     ram_data = []
#     all_compatible_ewes = set()
    
#     for ram_id in selected_ram_ids:
#         try:
#             ram = Sheep.objects.get(ear_tag_number=ram_id)
#             compatible_ewes = get_compatible_ewes(ram)
            
#             ram_data.append({
#                 'ram': ram,
#                 'compatible_ewes': compatible_ewes
#             })
#             selected_rams.append(ram)
            
#             for ewe in compatible_ewes:
#                 all_compatible_ewes.add(ewe)
                
#         except Sheep.DoesNotExist:
#             continue
    
#     # Get all available ewes for the incompatible list
#     all_ewes = get_available_ewes()
#     incompatible_ewes = [ewe for ewe in all_ewes if ewe not in all_compatible_ewes]
    
#     # Prepare data for template
#     context = {
#         'selected_rams': selected_rams,
#         'ram_data': ram_data,
#         'all_compatible_ewes': list(all_compatible_ewes),
#         'incompatible_ewes': incompatible_ewes,
#         'today': timezone.now().date(),  # Add current date for date inputs
#     }
#     return render(request, 'breeding/breeding_task.html', context)

# @login_required
# def breeding_task(request):
#     """Breeding task page with selected rams and compatible ewes"""
#     selected_ram_ids = request.GET.getlist('selected_rams')
    
#     if not selected_ram_ids:
#         messages.error(request, "No rams selected for breeding")
#         return redirect('breeding_home')  # Fixed: removed namespace
    
#     selected_rams = []
#     ram_data = []
#     all_compatible_ewes = set()
    
#     for ram_id in selected_ram_ids:
#         try:
#             ram = Sheep.objects.get(ear_tag_number=ram_id)
#             compatible_ewes = get_compatible_ewes(ram)
            
#             ram_data.append({
#                 'ram': ram,
#                 'compatible_ewes': compatible_ewes
#             })
#             selected_rams.append(ram)
            
#             for ewe in compatible_ewes:
#                 all_compatible_ewes.add(ewe)
                
#         except Sheep.DoesNotExist:
#             messages.warning(request, f"Ram with ID {ram_id} not found")
#             continue
    
#     # Get all available ewes for the incompatible list
#     all_ewes = get_available_ewes()
#     incompatible_ewes = [ewe for ewe in all_ewes if ewe not in all_compatible_ewes]
    
#     # Prepare data for template
#     context = {
#         'selected_rams': selected_rams,
#         'ram_data': ram_data,
#         'all_compatible_ewes': list(all_compatible_ewes),
#         'incompatible_ewes': incompatible_ewes,
#         'today': timezone.now().date(),  # Add current date for date inputs
#     }
#     return render(request, 'breeding/breeding_task.html', context)

# @login_required
# def breeding_info(request):
#     """Breeding information page with final planning"""
#     if request.method == 'POST':
#         selected_pairs = json.loads(request.POST.get('selected_pairs', '[]'))
        
#         breeding_data = []
#         for pair in selected_pairs:
#             try:
#                 ram = Sheep.objects.get(ear_tag_number=pair['ram_id'])
#                 ewe = Sheep.objects.get(ear_tag_number=pair['ewe_id'])
                
#                 from .services import predict_lamb_breed
#                 lamb_breed, lamb_breed_level = predict_lamb_breed(ewe, ram)
                
#                 breeding_data.append({
#                     'ram': ram,
#                     'ewe': ewe,
#                     'lamb_breed': lamb_breed,
#                     'lamb_breed_level': lamb_breed_level,
#                     'start_date': pair.get('start_date', ''),
#                 })
#             except Sheep.DoesNotExist:
#                 continue
        
#         context = {
#             'breeding_data': breeding_data,
#         }
#         return render(request, 'breeding/breeding_info.html', context)
    
#     return redirect('breeding:breeding_task')

# @login_required
# def breeding_info(request):
#     """Breeding information page with final planning"""
#     if request.method == 'POST':
#         try:
#             # Get the selected pairs data
#             selected_pairs_json = request.POST.get('selected_pairs', '[]')
            
#             # Parse the JSON data
#             selected_pairs = json.loads(selected_pairs_json)
            
#             # Validate that selected_pairs is a list
#             if not isinstance(selected_pairs, list):
#                 messages.error(request, "Invalid data format for selected pairs")
#                 return redirect('breeding_task')
            
#             breeding_data = []
#             for pair in selected_pairs:
#                 # Validate that pair is a dictionary
#                 if not isinstance(pair, dict):
#                     continue
                    
#                 try:
#                     ram_id = pair.get('ram_id')
#                     ewe_id = pair.get('ewe_id')
                    
#                     if not ram_id or not ewe_id:
#                         continue
                    
#                     ram = Sheep.objects.get(ear_tag_number=ram_id)
#                     ewe = Sheep.objects.get(ear_tag_number=ewe_id)
                    
#                     # Predict lamb breed
#                     lamb_breed, lamb_breed_level = predict_lamb_breed(ewe, ram)
                    
#                     breeding_data.append({
#                         'ram': ram,
#                         'ewe': ewe,
#                         'lamb_breed': lamb_breed,
#                         'lamb_breed_level': lamb_breed_level,
#                         'start_date': pair.get('start_date', ''),
#                     })
#                 except Sheep.DoesNotExist:
#                     messages.warning(request, f"One or more sheep not found: Ram {ram_id}, Ewe {ewe_id}")
#                     continue
#                 except KeyError as e:
#                     messages.warning(request, f"Missing data in pair: {e}")
#                     continue
            
#             if not breeding_data:
#                 messages.error(request, "No valid breeding pairs found in the submitted data")
#                 return redirect('breeding_task')
            
#             context = {
#                 'breeding_data': breeding_data,
#             }
#             return render(request, 'breeding/breeding_info.html', context)
            
#         except json.JSONDecodeError as e:
#             messages.error(request, f"Invalid JSON data: {str(e)}")
#             return redirect('breeding_task')
#         except Exception as e:
#             messages.error(request, f"Error processing breeding data: {str(e)}")
#             return redirect('breeding_task')
    
#     # If not POST, redirect to breeding task
#     return redirect('breeding_task')

# *******************************************************************************************************************
# @login_required
# def create_breeding_cycle(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             breeding_cycles = data.get('breeding_cycles', [])
#             created_cycles = []

#             for cycle_data in breeding_cycles:
#                 ewe_id = cycle_data.get('ewe_id')
#                 ram_id = cycle_data.get('ram_id')
#                 start_date_str = cycle_data.get('start_date')

#                 start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
#                 ewe = Sheep.objects.get(ear_tag_number=ewe_id)
#                 ram = Sheep.objects.get(ear_tag_number=ram_id)

#                 breeding_cycle = BreedingCycle(
#                     ewe=ewe,
#                     ram=ram,
#                     start_date=start_date,
#                     created_by=request.user
#                 )
#                 breeding_cycle.save()
#                 created_cycles.append(breeding_cycle.cycle_id)

#             return JsonResponse({
#                 'success': True,
#                 'message': f'Successfully created {len(created_cycles)} breeding cycles',
#                 'cycle_ids': created_cycles
#             })

#         except Exception as e:
#             return JsonResponse({'success': False, 'message': str(e)})

#     return JsonResponse({'success': False, 'message': 'Invalid request method'})

# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# @login_required
# def breeding_selection(request):
#     """Main breeding selection view with breed compatibility"""
#     rams = get_available_rams()
#     ewes = get_available_ewes()
    
#     selected_ram_id = request.GET.get('ram_id')
#     selected_ram = None
#     compatible_ewes = []
#     breed_compatibility_info = None
#     incompatible_ewes_info = []
    
#     if selected_ram_id:
#         try:
#             selected_ram = Sheep.objects.get(ear_tag_number=selected_ram_id)
#             compatible_ewes = get_compatible_ewes(selected_ram)
#             breed_compatibility_info = get_breed_compatibility_info(selected_ram)
            
#             # Get information about incompatible ewes for debugging
#             all_ewes = get_available_ewes()
#             for ewe in all_ewes:
#                 if ewe not in compatible_ewes:
#                     # Check if it's due to breed or family
#                     breed_ok = check_breed_compatibility(selected_ram, ewe)
#                     family_ok = check_for_inbreeding(ewe, selected_ram)
                    
#                     if not breed_ok:
#                         incompatible_ewes_info.append({
#                             'ewe': ewe.ear_tag_number,
#                             'breed': ewe.breed,
#                             'reason': f"Breed incompatibility: {selected_ram.breed} ram cannot mate with {ewe.breed} ewe"
#                         })
#                     elif not family_ok:
#                         relationships = get_family_relationship(ewe, selected_ram)
#                         incompatible_ewes_info.append({
#                             'ewe': ewe.ear_tag_number,
#                             'breed': ewe.breed,
#                             'reason': f"Family relationship: {', '.join(relationships)}"
#                         })
            
#         except Sheep.DoesNotExist:
#             pass
    
#     context = {
#         'rams': rams,
#         'ewes': ewes,
#         'selected_ram': selected_ram,
#         'compatible_ewes': compatible_ewes,
#         'breed_compatibility_info': breed_compatibility_info,
#         'incompatible_ewes_info': incompatible_ewes_info,
#     }
    
#     return render(request, 'breeding.html', context)

# # @login_required
# # def create_breeding_cycle(request):
# #     """Handle breeding cycle creation with breed prediction"""
# #     if request.method == 'POST':
# #         try:
# #             data = json.loads(request.body)
# #             ewe_id = data.get('ewe_id')
# #             ram_id = data.get('ram_id')
# #             start_date = data.get('start_date')
            
# #             ewe = Sheep.objects.get(ear_tag_number=ewe_id)
# #             ram = Sheep.objects.get(ear_tag_number=ram_id)
            
# #             # Double-check breed compatibility
# #             from .services import check_breed_compatibility
# #             if not check_breed_compatibility(ram, ewe):
# #                 return JsonResponse({
# #                     'success': False,
# #                     'message': f'Breed incompatibility: {ram.breed} ram cannot mate with {ewe.breed} ewe'
# #                 })
            
# #             # Double-check inbreeding prevention
# #             from .services import check_for_inbreeding
# #             if not check_for_inbreeding(ewe, ram):
# #                 relationships = get_family_relationship(ewe, ram)
# #                 return JsonResponse({
# #                     'success': False,
# #                     'message': f'Breeding not allowed: {", ".join(relationships)}'
# #                 })
            
# #             # Predict lamb breed
# #             lamb_breed, lamb_breed_level = predict_lamb_breed(ewe, ram)
            
# #             # Create breeding cycle
# #             breeding_cycle = BreedingCycle(
# #                 ewe=ewe,
# #                 ram=ram,
# #                 start_date=start_date,
# #                 created_by=request.user
# #             )
# #             breeding_cycle.save()
            
# #             # Add breed prediction to response
# #             breed_prediction_msg = ""
# #             if lamb_breed and lamb_breed_level:
# #                 breed_prediction_msg = f" Predicted lamb: {lamb_breed} ({lamb_breed_level}%)"
# #             else:
# #                 breed_prediction_msg = " Lamb breed requires manual assignment."
            
# #             return JsonResponse({
# #                 'success': True,
# #                 'message': f'Breeding cycle created successfully! Expected birth: {breeding_cycle.expected_birth_date}.{breed_prediction_msg}'
# #             })
            
# #         except Exception as e:
# #             return JsonResponse({
# #                 'success': False,
# #                 'message': str(e)
# #             })
    
# #     return JsonResponse({'success': False, 'message': 'Invalid request method'})

# @login_required
# def create_breeding_cycle(request):
#     """Handle breeding cycle creation with breed prediction"""
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             ewe_id = data.get('ewe_id')
#             ram_id = data.get('ram_id')
#             start_date_str = data.get('start_date')
            
#             # Convert string date to date object
#             try:
#                 start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
#             except (ValueError, TypeError):
#                 return JsonResponse({
#                     'success': False,
#                     'message': 'Invalid date format. Please use YYYY-MM-DD.'
#                 })
            
#             # Validate that start date is not in the past
#             if start_date < timezone.now().date():
#                 return JsonResponse({
#                     'success': False,
#                     'message': 'Start date cannot be in the past.'
#                 })
            
#             # Get the sheep objects
#             ewe = Sheep.objects.get(ear_tag_number=ewe_id)
#             ram = Sheep.objects.get(ear_tag_number=ram_id)
            
#             # Double-check breed compatibility
#             if not check_breed_compatibility(ram, ewe):
#                 return JsonResponse({
#                     'success': False,
#                     'message': f'Breed incompatibility: {ram.breed} ram cannot mate with {ewe.breed} ewe'
#                 })
            
#             # Double-check inbreeding prevention
#             if not check_for_inbreeding(ewe, ram):
#                 relationships = get_family_relationship(ewe, ram)
#                 return JsonResponse({
#                     'success': False,
#                     'message': f'Breeding not allowed: {", ".join(relationships)}'
#                 })
            
#             # Check ram capacity
#             if not check_ram_capacity(ram, start_date):
#                 return JsonResponse({
#                     'success': False,
#                     'message': f'Ram has exceeded breeding capacity for this season'
#                 })
            
#             # Predict lamb breed
#             lamb_breed, lamb_breed_level = predict_lamb_breed(ewe, ram)
            
#             # Create breeding cycle with proper date object
#             breeding_cycle = BreedingCycle(
#                 ewe=ewe,
#                 ram=ram,
#                 start_date=start_date,  # This is now a date object
#                 created_by=request.user
#             )
#             breeding_cycle.save()
            
#             # Add breed prediction to response
#             breed_prediction_msg = ""
#             if lamb_breed and lamb_breed_level:
#                 breed_prediction_msg = f" Predicted lamb: {lamb_breed} ({lamb_breed_level}%)"
#             else:
#                 breed_prediction_msg = " Lamb breed requires manual assignment."
            
#             return JsonResponse({
#                 'success': True,
#                 'message': f'Breeding cycle created successfully! Expected birth: {breeding_cycle.expected_birth_date}.{breed_prediction_msg}'
#             })
            
#         except Sheep.DoesNotExist:
#             return JsonResponse({
#                 'success': False,
#                 'message': 'Sheep not found'
#             })
#         except Exception as e:
#             return JsonResponse({
#                 'success': False,
#                 'message': f'Error: {str(e)}'
#             })
    
#     return JsonResponse({'success': False, 'message': 'Invalid request method'})

# @login_required
# def get_compatible_ewes_ajax(request, ram_id):
#     """AJAX endpoint to get compatible ewes for selected ram"""
#     try:
#         ram = Sheep.objects.get(ear_tag_number=ram_id)
#         compatible_ewes = get_compatible_ewes(ram)
#         breed_compatibility_info = get_breed_compatibility_info(ram)
        
#         ewes_data = []
#         for ewe in compatible_ewes:
#             # Predict lamb breed for each compatible ewe
#             lamb_breed, lamb_breed_level = predict_lamb_breed(ewe, ram)
            
#             ewes_data.append({
#                 'ear_tag_number': ewe.ear_tag_number,
#                 'breed': ewe.breed,
#                 'breed_level': ewe.breed_level,
#                 'type': ewe.type,
#                 'age_days': (timezone.now().date() - ewe.date_of_birth).days if ewe.date_of_birth else 'Unknown',
#                 'predicted_lamb_breed': lamb_breed,
#                 'predicted_lamb_level': lamb_breed_level
#             })
        
#         return JsonResponse({
#             'success': True,
#             'compatible_ewes': ewes_data,
#             'total_compatible': len(compatible_ewes),
#             'breed_compatibility_info': breed_compatibility_info
#         })
#     except Sheep.DoesNotExist:
#         return JsonResponse({
#             'success': False,
#             'message': 'Ram not found'
#         })
    


# # ////////////////////////////////////////////////////////////////////////////////////////

# class BreedingCycleListView(ListView):
#     model = BreedingCycle
#     template_name = 'breeding_cycle_list.html'
#     context_object_name = 'cycles'
#     paginate_by = 20
    
#     def get_queryset(self):
#         queryset = BreedingCycle.objects.select_related('ewe', 'ram').all()
        
#         # Filtering
#         status_filter = self.request.GET.get('status')
#         if status_filter:
#             queryset = queryset.filter(status=status_filter)
        
#         # Search
#         search_query = self.request.GET.get('search')
#         if search_query:
#             queryset = queryset.filter(
#                 Q(cycle_id__icontains=search_query) |
#                 Q(ewe__ear_tag_number__icontains=search_query) |
#                 Q(ram__ear_tag_number__icontains=search_query)
#             )
        
#         # Sorting
#         sort_by = self.request.GET.get('sort', '-start_date')
#         return queryset.order_by(sort_by)
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['status_choices'] = BreedingCycle.STATUS_CHOICES
#         context['current_filters'] = {
#             'status': self.request.GET.get('status', ''),
#             'search': self.request.GET.get('search', ''),
#         }
#         return context

# class BreedingCycleDetailView(DetailView):
#     model = BreedingCycle
#     template_name = 'breeding_cycle_detail.html'
#     context_object_name = 'cycle'
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         cycle = self.get_object()
        
#         # Get lambs from this cycle
#         context['lambs'] = Sheep.objects.filter(
#             parent_ewe=cycle.ewe,
#             parent_ram=cycle.ram,
#             date_of_birth=cycle.actual_birth_date
#         )
        
#         # Get related records
#         context['audit_logs'] = AuditLog.objects.filter(
#             entity='BreedingCycle',
#             entity_id=cycle.cycle_id
#         ).order_by('-timestamp')[:10]
        
#         return context

# class BreedingCycleCreateView(CreateView):
#     model = BreedingCycle
#     template_name = 'breeding_cycle_form.html'
#     fields = ['ewe', 'ram', 'start_date', 'notes']
    
#     def form_valid(self, form):
#         # Generate cycle ID
#         form.instance.cycle_id = f"CYCLE_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
#         # Validate breeding pair
#         ewe = form.cleaned_data['ewe']
#         ram = form.cleaned_data['ram']
        
#         # Check if both are healthy
#         if not ewe.is_healthy or not ram.is_healthy:
#             form.add_error(None, "Both ewe and ram must be healthy for breeding")
#             return self.form_invalid(form)
        
#         # Check ram capacity
#         from .services import check_ram_capacity
#         capacity_ok, message = check_ram_capacity(ram)
#         if not capacity_ok:
#             form.add_error('ram', message)
#             return self.form_invalid(form)
        
#         # Check inbreeding prevention
#         from .services import check_inbreeding
#         inbreeding_ok, relationship = check_inbreeding(ewe, ram)
#         if not inbreeding_ok:
#             form.add_error(None, f"Inbreeding prevention: {relationship} relationship detected")
#             return self.form_invalid(form)
        
#         response = super().form_valid(form)
        
#         # Log the creation
#         AuditLog.objects.create(
#             user_id=self.request.user.username,
#             action='CREATE_BREEDING_CYCLE',
#             entity='BreedingCycle',
#             entity_id=form.instance.cycle_id,
#             new_values={
#                 'ewe': ewe.ear_tag_number,
#                 'ram': ram.ear_tag_number,
#                 'start_date': form.instance.start_date.isoformat(),
#                 'status': form.instance.status
#             }
#         )
        
#         return response
    
#     def get_success_url(self):
#         return reverse_lazy('breeding_cycle_detail', kwargs={'pk': self.object.cycle_id})

# class BreedingCycleUpdateView(UpdateView):
#     model = BreedingCycle
#     template_name = 'breeding_cycle_form.html'
#     fields = ['status', 'actual_birth_date', 'cancellation_reason', 'notes']
    
#     def form_valid(self, form):
#         old_status = self.get_object().status
#         old_birth_date = self.get_object().actual_birth_date
        
#         response = super().form_valid(form)
        
#         # Log status changes
#         if old_status != form.instance.status:
#             AuditLog.objects.create(
#                 user_id=self.request.user.username,
#                 action='UPDATE_BREEDING_CYCLE_STATUS',
#                 entity='BreedingCycle',
#                 entity_id=form.instance.cycle_id,
#                 old_values={'status': old_status},
#                 new_values={'status': form.instance.status},
#                 notes=form.instance.cancellation_reason if form.instance.status == 'CANCELLED' else ''
#             )
        
#         # Log birth date recording
#         if not old_birth_date and form.instance.actual_birth_date:
#             AuditLog.objects.create(
#                 user_id=self.request.user.username,
#                 action='RECORD_BIRTH_DATE',
#                 entity='BreedingCycle',
#                 entity_id=form.instance.cycle_id,
#                 new_values={'actual_birth_date': form.instance.actual_birth_date.isoformat()}
#             )
        
#         return response
    
#     def get_success_url(self):
#         return reverse_lazy('breeding_cycle_detail', kwargs={'pk': self.object.cycle_id})

# class BreedingDashboardView(TemplateView):
#     template_name = 'breeding_dashboard.html'
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         today = timezone.now().date()
        
#         # Active cycles
#         context['active_cycles'] = BreedingCycle.objects.filter(
#             status__in=['PLANNED', 'IN_PROGRESS']
#         ).select_related('ewe', 'ram').order_by('expected_birth_date')
        
#         # Upcoming births (next 30 days)
#         context['upcoming_births'] = BreedingCycle.objects.filter(
#             status='IN_PROGRESS',
#             expected_birth_date__range=[today, today + timedelta(days=30)]
#         ).select_related('ewe', 'ram')
        
#         # Overdue births
#         context['overdue_births'] = BreedingCycle.objects.filter(
#             status='IN_PROGRESS',
#             expected_birth_date__lt=today
#         ).select_related('ewe', 'ram')
        
#         # Statistics
#         context['total_cycles'] = BreedingCycle.objects.count()
#         context['completed_cycles'] = BreedingCycle.objects.filter(status='COMPLETED').count()
#         context['success_rate'] = (
#             (context['completed_cycles'] / context['total_cycles'] * 100) 
#             if context['total_cycles'] > 0 else 0
#         )
        
#         # Ram utilization
#         rams = Sheep.objects.filter(sex='MALE', type__in=['RAM', 'YOUNG_RAM'])
#         ram_utilization = []
#         for ram in rams:
#             active_cycles = BreedingCycle.objects.filter(
#                 ram=ram, 
#                 status__in=['PLANNED', 'IN_PROGRESS']
#             ).count()
#             capacity = 55 if ram.breed == 'PD' else 40
#             utilization = (active_cycles / capacity * 100) if capacity > 0 else 0
#             ram_utilization.append({
#                 'ram': ram,
#                 'active_cycles': active_cycles,
#                 'capacity': capacity,
#                 'utilization': utilization,
#                 'is_over_capacity': active_cycles > capacity
#             })
        
#         context['ram_utilization'] = ram_utilization
        
#         # Breed distribution forecast
#         active_with_breed = BreedingCycle.objects.filter(
#             status__in=['PLANNED', 'IN_PROGRESS']
#         ).select_related('ewe', 'ram')
        
#         breed_forecast = {}
#         for cycle in active_with_breed:
#             lamb_breed, _ = predict_lamb_breed(cycle.ewe, cycle.ram)
#             breed_forecast[lamb_breed] = breed_forecast.get(lamb_breed, 0) + 1
        
#         context['breed_forecast'] = breed_forecast
        
#         return context