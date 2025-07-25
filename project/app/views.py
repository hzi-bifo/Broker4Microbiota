from django import forms
import json
import logging
import importlib
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.generic import ListView
from django.forms import CheckboxSelectMultiple, CheckboxInput, DateInput, modelformset_factory
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .forms import OrderForm, SampleForm, SamplesetForm, ProjectForm
from .models import Order, Sample, Sampleset, Project, Assembly, Bin, STATUS_CHOICES, SAMPLE_TYPE_NORMAL, SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG, SiteSettings
from .models import Order, Sample, Sampleset, Project, STATUS_CHOICES, SAMPLE_TYPE_NORMAL, SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG, SiteSettings
from django_q.tasks import async_task, result
from .hooks import process_submg_result_inner, process_mag_result_inner

from json.decoder import JSONDecodeError
from django.conf import settings
from django.http import Http404

logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}! You have successfully logged in.')
            # Handle next URL if provided
            next_url = request.GET.get('next', 'project_list')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password. Please check your credentials and try again.')
            return render(request, 'login.html', {'form': form})
    else:
        if request.user.is_authenticated:
            return redirect('project_list')
        else:
            form = AuthenticationForm()
            return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created successfully. You can now submit sequencing orders.')
            return redirect('project_list')
        else:
            # Extract and display specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.capitalize()}: {error}')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

class ProjectListView(ListView):
    model = Project
    template_name = 'project_list.html'
    context_object_name = 'projects'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        projects = Project.objects.filter(user=self.request.user)
        return projects
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if user has any samples across all projects
        has_samples = Sample.objects.filter(order__project__user=self.request.user).exists()
        context['has_samples'] = has_samples
        context['site_settings'] = SiteSettings.get_settings()
        
        # Add sample count for each project
        for project in context['projects']:
            sample_count = Sample.objects.filter(order__project=project).count()
            project.sample_count = sample_count
        
        return context

def project_view(request, project_id=None):
    if request.user.is_authenticated:
        if project_id:
            project = get_object_or_404(Project, pk=project_id, user=request.user)
            form = ProjectForm(instance=project)           
        else:
            form = ProjectForm()

        if request.method == 'POST':
            if project_id:
                form = ProjectForm(request.POST, instance=project)
            else:
                form = ProjectForm(request.POST)

            if form.is_valid():
                project = form.save(commit=False)
                project.user = request.user
                project.save()

                return redirect('project_list')

        return render(request, 'project_form.html', {'form': form})
    else:
        return redirect('login')

def delete_project(request, project_id):
    if request.user.is_authenticated:
        project = get_object_or_404(Project, pk=project_id, user=request.user)
        project.delete()

        return redirect('project_list')   
    else:
        return redirect('login')


class OrderListView(ListView):
    model = Order
    template_name = 'order_list.html'
    context_object_name = 'orders'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, pk=project_id, user=self.request.user)

        orders = Order.objects.filter(project=project)
        return orders

    def get_context_data(self, **kwargs):
        # Add project_id and project to the context
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, pk=project_id, user=self.request.user)
        context['project_id'] = project_id
        context['project'] = project
        context['site_settings'] = SiteSettings.get_settings()
        
        # Add user-visible notes and field selection info for each order
        for order in context['orders']:
            # Get the latest user-visible note (especially rejections)
            latest_note = order.notes.filter(
                note_type__in=['user_visible', 'rejection']
            ).order_by('-created_at').first()
            order.latest_user_note = latest_note
            
            # Get field selection info
            sample_set = order.sampleset_set.filter(sample_type=SAMPLE_TYPE_NORMAL).first()
            if sample_set and sample_set.checklists:
                checklist_name = sample_set.checklists[0] if sample_set.checklists else None
                if checklist_name and checklist_name in Sampleset.checklist_structure:
                    # Get readable name - handle GSC MIxS specially
                    readable_name = checklist_name.replace('_', ' ')
                    if readable_name.startswith('GSC MIxS'):
                        readable_name = 'GSC MIxS ' + readable_name[8:].strip().title()
                    else:
                        readable_name = readable_name.title()
                    
                    # Count fields
                    checklist_item = Sampleset.checklist_structure[checklist_name]
                    checklist_class_name = checklist_item['checklist_class_name']
                    checklist_class = getattr(importlib.import_module("app.models"), checklist_class_name)
                    
                    # Get all fields
                    all_fields = checklist_class._meta.get_fields()
                    relevant_fields = [f for f in all_fields 
                                     if f.name not in ['id', 'sampleset', 'sample', 'sample_type']]
                    total_fields = len(relevant_fields)
                    
                    # Count mandatory fields
                    mandatory_fields = sum(1 for f in relevant_fields 
                                         if hasattr(f, 'blank') and not f.blank)
                    
                    if sample_set.selected_fields:
                        # Count selected optional fields
                        selected_optional = sum(1 for f in relevant_fields 
                                              if hasattr(f, 'blank') and f.blank and 
                                              sample_set.selected_fields.get(f.name, False))
                        
                        order.metadata_info = {
                            'checklist_name': readable_name,
                            'mandatory': mandatory_fields,
                            'selected_optional': selected_optional,
                            'total': total_fields,
                            'has_selection': True
                        }
                    else:
                        # No field selection made yet - all fields are selected by default
                        order.metadata_info = {
                            'checklist_name': readable_name,
                            'mandatory': mandatory_fields,
                            'selected_optional': total_fields - mandatory_fields,  # All optional fields
                            'total': total_fields,
                            'has_selection': False
                        }
                else:
                    order.metadata_info = None
            else:
                order.metadata_info = None
        
        return context

def order_view(request, project_id=None, order_id=None):
    if request.user.is_authenticated:
        project = get_object_or_404(Project, pk=project_id, user=request.user)

        if order_id:
            order = get_object_or_404(Order, pk=order_id, project=project)
            form = OrderForm(instance=order)           
        else:
            form = OrderForm()

        if request.method == 'POST':
            if order_id:
                form = OrderForm(request.POST, instance=order)
            else:
                form = OrderForm(request.POST)

            if form.is_valid():
                order = form.save(commit=False)
                order.project = project
                order.save()
                
                messages.success(request, f'Order #{order.id} has been created successfully!')
                return redirect('order_list', project_id=project_id)
            else:
                messages.error(request, 'Please correct the errors below before submitting the form.')
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field.capitalize()}: {error}')

        return render(request, 'order_form.html', {'form': form, 'project_id': project_id})
    else:
        return redirect('login')

def delete_order(request, project_id, order_id):
    if request.user.is_authenticated:
        project = get_object_or_404(Project, pk=project_id, user=request.user)

        order = get_object_or_404(Order, pk=order_id, project=project)
        order.delete()

        return redirect('order_list', project_id=order.project.id)   
    else:
        return redirect('login')

def metadata_view(request, project_id, order_id):
    
    if request.user.is_authenticated:
        project = get_object_or_404(Project, pk=project_id, user=request.user)

        order = get_object_or_404(Order, pk=order_id, project=project)

        # should only be one
        sample_set = order.sampleset_set.filter(sample_type=SAMPLE_TYPE_NORMAL).first()
        if not sample_set:
            sample_set = Sampleset(order=order, sample_type=SAMPLE_TYPE_NORMAL) 
        form = SamplesetForm(instance=sample_set)
        
        if request.method == 'POST':

            # Check for any samples for order
            samples = order.sample_set.filter()
            has_samples = samples.exists()
            
            # Store the previous checklist for comparison BEFORE form processing
            # sample_set.pk check ensures we're dealing with an existing record
            previous_checklists = sample_set.checklists.copy() if (sample_set and sample_set.pk and sample_set.checklists) else []

            if order_id:
                form = SamplesetForm(request.POST, instance=sample_set)
            else:
                form = SamplesetForm(request.POST)

            if form.is_valid():
                sample_set = form.save(commit=False)
                sample_set.user = request.user
                sample_set.save()
                
                # Check if checklist has changed and samples exist
                new_checklists = sample_set.checklists or []
                
                # Convert both to sets for comparison, handling None and empty lists
                prev_set = set(previous_checklists) if previous_checklists else set()
                new_set = set(new_checklists) if new_checklists else set()
                
                # Only consider it a "change" if there was a previous checklist AND it's different
                # Initial checklist selection (from empty to something) should not trigger the warning
                checklist_changed = bool(prev_set) and (prev_set != new_set)
                
                # Debug logging
                logger.info(f"Order {order_id}: Previous checklists: {previous_checklists} (set: {prev_set}), New checklists: {new_checklists} (set: {new_set}), Changed: {checklist_changed}, Has samples: {has_samples}")
                
                if checklist_changed and has_samples:
                    # Clear all MIxS-specific data from existing samples
                    for sample_type in [SAMPLE_TYPE_NORMAL, SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG]:
                        # Get all sample sets for this order
                        sample_sets = order.sampleset_set.filter(sample_type=sample_type)
                        
                        for ss in sample_sets:
                            # Delete all existing checklist instances for both previous and new checklists
                            # This ensures clean slate even if switching back to a previously used checklist
                            all_checklists = set(previous_checklists or []) | set(new_checklists)
                            for checklist_name in all_checklists:
                                if checklist_name in Sampleset.checklist_structure:
                                    checklist_info = Sampleset.checklist_structure[checklist_name]
                                    checklist_class_name = checklist_info['checklist_class_name']
                                    unitchecklist_class_name = checklist_info['unitchecklist_class_name']
                                    
                                    # Delete checklist instances
                                    try:
                                        checklist_class = getattr(importlib.import_module("app.models"), checklist_class_name)
                                        checklist_class.objects.filter(sampleset=ss).delete()
                                    except:
                                        pass
                                    
                                    # Delete unit checklist instances
                                    try:
                                        unitchecklist_class = getattr(importlib.import_module("app.models"), unitchecklist_class_name)
                                        unitchecklist_class.objects.filter(sampleset=ss).delete()
                                    except:
                                        pass
                    
                    # Mark order as having incomplete sample data
                    order.checklist_changed = True
                    order.save()
                    
                    messages.warning(request, 'MIxS checklist changed. All checklist-specific sample data has been cleared. Please update your samples with the new checklist fields.')
                elif not checklist_changed and order.checklist_changed:
                    # If checklist hasn't changed but the flag was previously set, don't clear it
                    # This ensures the warning persists until samples are actually updated
                    logger.info(f"Order {order_id}: Checklist not changed, keeping checklist_changed flag as True")

                assembly_sample_set = order.sampleset_set.filter(sample_type=SAMPLE_TYPE_ASSEMBLY).first()
                if not assembly_sample_set:
                    assembly_sample_set = Sampleset(order=order, sample_type=SAMPLE_TYPE_ASSEMBLY) 
                assembly_sample_set.checklists = sample_set.checklists
                assembly_sample_set.include = ""
                assembly_sample_set.exclude = ""
                assembly_sample_set.custom = ""
                assembly_sample_set.save()
                bin_sample_set = order.sampleset_set.filter(sample_type=SAMPLE_TYPE_BIN).first()
                if not bin_sample_set:
                    bin_sample_set = Sampleset(order=order, sample_type=SAMPLE_TYPE_BIN)
                bin_sample_set.checklists = [settings.BIN_CHECKLIST]
                bin_sample_set.include = ""
                bin_sample_set.exclude = ""
                bin_sample_set.custom = ""
                bin_sample_set.save()
                mag_sample_set = order.sampleset_set.filter(sample_type=SAMPLE_TYPE_MAG).first()
                if not mag_sample_set:
                    mag_sample_set = Sampleset(order=order, sample_type=SAMPLE_TYPE_MAG)
                mag_sample_set.checklists = [settings.MAG_CHECKLIST]
                mag_sample_set.include = ""
                mag_sample_set.exclude = ""
                mag_sample_set.custom = ""
                mag_sample_set.save()

                # Clear selected_fields when checklist changes to force user to reselect fields
                sample_set.selected_fields = {}
                sample_set.save()
                
                return redirect('field_selection_view', project_id=project_id, order_id=order_id)
            
        # Get field selection info if it exists
        field_selection_info = {}
        if sample_set and sample_set.checklists:
            for checklist_name in sample_set.checklists:
                if checklist_name in Sampleset.checklist_structure:
                    checklist_item = Sampleset.checklist_structure[checklist_name]
                    checklist_class_name = checklist_item['checklist_class_name']
                    checklist_class = getattr(importlib.import_module("app.models"), checklist_class_name)
                    
                    # Get all fields
                    all_fields = checklist_class._meta.get_fields()
                    relevant_fields = [f for f in all_fields 
                                     if f.name not in ['id', 'sampleset', 'sample', 'sample_type']]
                    total_fields = len(relevant_fields)
                    
                    # Count mandatory fields
                    mandatory_fields = sum(1 for f in relevant_fields 
                                         if hasattr(f, 'blank') and not f.blank)
                    
                    if sample_set.selected_fields:
                        # Count selected optional fields
                        selected_optional = sum(1 for f in relevant_fields 
                                              if hasattr(f, 'blank') and f.blank and 
                                              sample_set.selected_fields.get(f.name, False))
                        
                        field_selection_info[checklist_name] = {
                            'total': total_fields,
                            'mandatory': mandatory_fields,
                            'selected_optional': selected_optional,
                            'total_selected': mandatory_fields + selected_optional,
                            'name': checklist_name.replace('_', ' ').title()
                        }
        
        return render(request, 'metadata.html', {
            'sample_set': sample_set, 
            'project_id': project_id,
            'order_id': order_id,
            'field_selection_info': json.dumps(field_selection_info) if field_selection_info else '{}'
        })
    else:
        return redirect('login')

def field_selection_view(request, project_id, order_id, checklist=None):
    """View for selecting which fields from the checklist to include in the sample data collection."""
    
    if request.user.is_authenticated:
        # Import field descriptions
        try:
            from .field_descriptions import FIELD_DESCRIPTIONS
        except ImportError:
            FIELD_DESCRIPTIONS = {}
            
        project = get_object_or_404(Project, pk=project_id, user=request.user)
        order = get_object_or_404(Order, pk=order_id, project=project)
        
        # Get the sampleset for this order
        sample_set = order.sampleset_set.filter(sample_type=SAMPLE_TYPE_NORMAL).first()
        
        # Determine which checklist to use
        if checklist:
            # Use the passed checklist parameter
            checklists_to_use = [checklist]
        elif sample_set and sample_set.checklists:
            # Use the saved checklist
            checklists_to_use = sample_set.checklists
        else:
            # No checklist available, redirect back
            return redirect('metadata_view', project_id=project_id, order_id=order_id)
        
        if request.method == 'POST':
            # Process field selection
            selected_fields = {}
            
            # Get all field selections from POST data
            for key, value in request.POST.items():
                if key.startswith('field_'):
                    field_name = key[6:]  # Remove 'field_' prefix
                    selected_fields[field_name] = value == 'on'
            
            # If we're using a different checklist than saved, create/update sample_set
            if not sample_set:
                sample_set = Sampleset(
                    order=order, 
                    sample_type=SAMPLE_TYPE_NORMAL,
                    checklists=[checklist] if checklist else [],
                    include=[],  # Required field
                    exclude=[],  # Required field
                    custom=[]    # Required field
                )
            
            # Update checklist if provided via URL parameter
            if checklist and (not sample_set.checklists or checklist not in sample_set.checklists):
                sample_set.checklists = [checklist]
            
            # Save the selections
            sample_set.selected_fields = selected_fields
            sample_set.save()
            
            return redirect('order_list', project_id=project_id)
        
        # Prepare field data for the template
        field_data = []
        for checklist_name in checklists_to_use:
            if checklist_name in Sampleset.checklist_structure:
                checklist_item = Sampleset.checklist_structure[checklist_name]
                checklist_class_name = checklist_item['checklist_class_name']
                
                # Get the model class
                checklist_class = getattr(importlib.import_module("app.models"), checklist_class_name)
                
                # Get all fields from the model
                for field in checklist_class._meta.get_fields():
                    if field.name not in ['id', 'sampleset', 'sample', 'name', 'sample_type']:
                        # Use full description from XML if available, otherwise fall back to model help_text
                        help_text = FIELD_DESCRIPTIONS.get(field.name, '')
                        if not help_text and hasattr(field, 'help_text'):
                            help_text = field.help_text or ''
                            
                        # Check if we should show the field code (only if name is different from verbose name)
                        verbose_name_normalized = field.verbose_name.lower().replace(' ', '_').replace('-', '_')
                        show_code = field.name != verbose_name_normalized
                        
                        # Determine if field is required
                        is_required = not field.blank if hasattr(field, 'blank') else False
                        
                        # Determine if field is selected
                        if is_required:
                            # Required fields are always selected
                            is_selected = True
                        elif checklist and (not sample_set or checklist not in (sample_set.checklists or [])):
                            # If showing a different checklist than saved, default to all selected
                            is_selected = True
                        elif sample_set and sample_set.selected_fields:
                            # If we have saved selections, use them (default to False for unspecified)
                            is_selected = sample_set.selected_fields.get(field.name, False)
                        else:
                            # If no selections saved yet, default to True (all fields selected)
                            is_selected = True
                        
                        field_info = {
                            'name': field.name,
                            'verbose_name': field.verbose_name,
                            'required': is_required,
                            'help_text': help_text,
                            'checklist': checklist_name,
                            'show_code': show_code,
                            'selected': is_selected
                        }
                        field_data.append(field_info)
        
        context = {
            'project': project,
            'order': order,
            'sample_set': sample_set,
            'field_data': field_data,
            'project_id': project_id,
            'order_id': order_id,
            'checklist_from_url': checklist,  # The checklist passed via URL
            'current_checklist': checklists_to_use[0] if checklists_to_use else None  # The checklist being displayed
        }
        
        return render(request, 'field_selection.html', context)
    else:
        return redirect('login')

def samples_view(request, project_id, order_id, sample_type):

    if request.user.is_authenticated:
        # Allow staff/admin users to access any project
        if request.user.is_staff or request.user.is_superuser:
            project = get_object_or_404(Project, pk=project_id)
        else:
            project = get_object_or_404(Project, pk=project_id, user=request.user)

        order = get_object_or_404(Order, pk=order_id, project=project)
        
        # Check if accessed from admin dashboard
        from_admin = request.GET.get('from_admin', 'false').lower() == 'true'

        if not (sample_type in [SAMPLE_TYPE_NORMAL, SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG]):
            raise Http404()

        # Get the sample set early so we can determine inclusions/exclusions
        sample_set = order.sampleset_set.filter(sample_type=sample_type).first()
        
        # For assembly/bin samples, use the normal sample's sampleset to get checklist configuration
        if not sample_set and sample_type in [SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG]:
            sample_set = order.sampleset_set.filter(sample_type=SAMPLE_TYPE_NORMAL).first()
        
        # Determine inclusions and exclusions based on field selection or legacy logic
        if sample_set and sample_set.selected_fields:
            # Build inclusions list: ALL required fields + selected optional fields
            inclusions = []
            
            # First, get essential fields from Sample model
            sample_model = Sample
            # Always include these essential Sample fields
            essential_sample_fields = ['sample_id', 'tax_id', 'scientific_name', 'sample_alias', 
                                     'sample_title', 'sample_description', 'status']
            
            # Add assembly-specific fields if this is an assembly sample
            if sample_type == SAMPLE_TYPE_ASSEMBLY:
                essential_sample_fields.append('assembly')
            for field_name in essential_sample_fields:
                if field_name not in inclusions:
                    inclusions.append(field_name)
            
            # Then check for any other selected fields from Sample model
            for field in sample_model._meta.get_fields():
                if field.name not in ['id', 'order', 'sampleset', 'sample_type'] + essential_sample_fields:
                    # Include if explicitly selected
                    if sample_set.selected_fields.get(field.name, False):
                        inclusions.append(field.name)
            
            # Then, get required and selected fields from checklist models
            for checklist_name in sample_set.checklists:
                if checklist_name in Sampleset.checklist_structure:
                    checklist_item = Sampleset.checklist_structure[checklist_name]
                    checklist_class_name = checklist_item['checklist_class_name']
                    checklist_class = getattr(importlib.import_module("app.models"), checklist_class_name)
                    
                    for field in checklist_class._meta.get_fields():
                        if field.name not in ['id', 'sampleset', 'sample', 'sample_type']:
                            # Include all non-blank (required) fields
                            if hasattr(field, 'blank') and not field.blank:
                                if field.name not in inclusions:
                                    inclusions.append(field.name)
                            # Also include if explicitly selected
                            elif sample_set.selected_fields.get(field.name, False):
                                if field.name not in inclusions:
                                    inclusions.append(field.name)
            
            exclusions = []
        else:
            # Fall back to old exclusion-based approach for backward compatibility
            inclusions = []
            exclusions = []
            
            if sample_type == SAMPLE_TYPE_NORMAL:
                exclusions = "assembly,bin"
            elif sample_type == SAMPLE_TYPE_ASSEMBLY:
                exclusions = "bin_identifier"
            elif sample_type == SAMPLE_TYPE_BIN:
                exclusions = "assembly"
            elif sample_type == SAMPLE_TYPE_MAG:
                exclusions = "assembly,bin"

        if request.method == 'POST':
            try:
                sample_data = json.loads(request.POST.get('sample_data'))

                print(f"Received sample_data: {sample_data}")

                # sample_set should already be fetched above, but verify it exists
                if not sample_set:
                    return JsonResponse({'success': False, 'error': 'Sample set not found'}, status=400)

                checklists = sample_set.checklists
            
                # Delete all existing checklists for the order
                for checklist in checklists:
                    checklist_name = checklist
                    checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  
                    checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
                    checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
                    
                    # Always use SAMPLE_TYPE_NORMAL for checklist entries
                    checklist_sample_type = SAMPLE_TYPE_NORMAL if sample_type in [SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG] else sample_type
                    try:
                        checklist_item_class.objects.filter(sampleset=sample_set, sample_type=checklist_sample_type).delete()
                    except:
                        pass

                    unitchecklist_class_name = Sampleset.checklist_structure[checklist_name]['unitchecklist_class_name']
                    unitchecklist_item_class =  getattr(importlib.import_module("app.models"), unitchecklist_class_name)
                    
                    try:
                        unitchecklist_item_class.objects.filter(sampleset=sample_set, sample_type=checklist_sample_type).delete()
                    except:
                        pass


                # Delete all existing samples for the order
                try:
                    Sample.objects.filter(order=order, sample_type=sample_type).delete()
                except: 
                    pass
                
                # Create new samples based on the received data
                for sample_info in sample_data:

                    sample=Sample(order = order, sample_type=sample_type)
                    sample.setFieldsFromResponse(sample_info, inclusions)
                    sample.sampleset = sample_set
                    sample.save()

                    # create new checklists based on the received data
                    for checklist in checklists:
                        try:
                            checklist_name = checklist
                            checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  
                            checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
                            checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
                            # Always use SAMPLE_TYPE_NORMAL for checklist entries
                            checklist_sample_type = SAMPLE_TYPE_NORMAL if sample_type in [SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG] else sample_type
                            checklist_item_instance = checklist_item_class(sampleset = sample_set, sample = sample, sample_type=checklist_sample_type)
                            checklist_item_instance.setFieldsFromResponse(sample_info, inclusions)
                            checklist_item_instance.save()
                            unitchecklist_class_name = Sampleset.checklist_structure[checklist_name]['unitchecklist_class_name']
                            unitchecklist_item_class =  getattr(importlib.import_module("app.models"), unitchecklist_class_name)
                            unitchecklist_item_instance = unitchecklist_item_class(sampleset = sample_set, sample = sample, sample_type=checklist_sample_type)
                            # unitchecklist_item_instance.setFieldsFromResponse(sample_info)
                            unitchecklist_item_instance.save()
                        except Exception as checklist_error:
                            print(f"Error creating checklist {checklist_name} for sample {sample.id}: {str(checklist_error)}")
                            # Continue with other checklists even if one fails
                            continue

                    print(f"Processing sample {sample.id}")

                    # print(sample.getAttributes(inclusions, exclusions))
                
                # Clear the checklist_changed flag since samples have been updated
                if order.checklist_changed:
                    order.checklist_changed = False
                    order.save()

                return JsonResponse({'success': True})
            
            except Exception as e:
                print(f"Error in samples_view POST: {str(e)}")
                logger.error(f"Error saving samples: {str(e)}", exc_info=True)
                return JsonResponse({'success': False, 'error': str(e)}, status=500)

        samples = order.sample_set.filter(sample_type=sample_type).order_by('sample_id')

        print(f"Retrieved samples: {list(samples)}")

        checklists = sample_set.checklists if sample_set else []
        
        extra_choices = []
        if sample_type == SAMPLE_TYPE_ASSEMBLY:
            assemblies = Assembly.objects.filter(order=order)
            for assembly in assemblies:
                extra_choices.append(f"{assembly.id}")
        elif sample_type == SAMPLE_TYPE_BIN:
            bins = Bin.objects.filter(order=order)
            for bin in bins:
                extra_choices.append(f"{bin.id}")

        validators = ""

        nested_headers = []
        nested_headers_checklists = []
        nested_headers_fields = []

        headers_size = []

        headers_max_size = 0

        # construct headers and array (to pass data back in POST) for HoT, for samples
        samples_headers = f"[\n"
        sample_headers_array = ""
        index = 2 # make space for delete button and unsaved indicator

        pixelsPerChar = settings.PIXELS_PER_CHAR

        nested_headers_checklists.append({'label': '', 'colspan': 2})
        nested_headers_fields = ['Delete', 'Saved']
        headers_size = [75,60]

        samples_headers = samples_headers + f"{{ title: 'Delete', renderer: deleteButtonRenderer }},\n{{ title: 'Saved', data: 'status', readOnly: true, renderer: statusRenderer }},\n"
        sample_headers_array = sample_headers_array + f"Delete: row[1],\nunsaved: row[1],\n"

        sample=Sample(order = order, sample_type=sample_type)

        samples_headers = samples_headers + sample.getHeaders(inclusions, exclusions, extra_choices)
        (index, sample_headers_array_update) = sample.getHeadersArray(index, inclusions, exclusions)
        sample_headers_array = sample_headers_array + sample_headers_array_update

        validators = validators + sample.getValidators(inclusions, exclusions)

        headers_count = sample.getHeadersCount(inclusions, exclusions)
        nested_headers_checklists.append({'label': 'sample', 'colspan': headers_count})
        nested_headers_fields.extend(sample.getHeaderNames(inclusions, exclusions))
        headers_size.extend(sample.getHeadersSize(pixelsPerChar, inclusions, exclusions))

        headers_max_size = sample.getHeadersMaxSize(headers_max_size, inclusions, exclusions)

        # Build field metadata for the UI
        field_metadata = {}
        
        # Get metadata for Sample fields
        sample_model = Sample
        for field_obj in sample_model._meta.get_fields():
            if hasattr(field_obj, 'name') and hasattr(field_obj, 'help_text'):
                field_name = field_obj.name
                field_info = {
                    'name': field_name,
                    'label': sample.fields.get(field_name, field_name),
                    'help_text': field_obj.help_text or '',
                    'required': not field_obj.blank if hasattr(field_obj, 'blank') else False,
                    'max_length': getattr(field_obj, 'max_length', None),
                    'choices': None,
                    'validator_pattern': None
                }
                
                # Apply field overrides if they exist
                if sample_set and sample_set.field_overrides and field_name in sample_set.field_overrides:
                    overrides = sample_set.field_overrides[field_name]
                    if 'required' in overrides:
                        field_info['required'] = overrides['required']
                
                # Check for choices
                if hasattr(field_obj, 'choices') and field_obj.choices:
                    field_info['choices'] = [{'value': c[0], 'label': c[1]} for c in field_obj.choices]
                
                # Check for validators
                if hasattr(field_obj, 'validators') and field_obj.validators:
                    for validator in field_obj.validators:
                        if hasattr(validator, 'regex'):
                            field_info['validator_pattern'] = validator.regex.pattern
                            break
                
                field_metadata[field_name] = field_info
        
        # construct headers and array (to pass data back in POST) for HoT, for checklists
        checklist_entries_list = []
        for checklist in checklists:

            checklist_name = checklist
            checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  

            # get the checklist model name from Checklist_structure 
            checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']

            checklist_entries_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
            samples_headers = samples_headers + checklist_entries_class().getHeaders(inclusions, exclusions)
            (index, sample_headers_array_update) = checklist_entries_class().getHeadersArray(index, inclusions, exclusions)
            sample_headers_array = sample_headers_array + sample_headers_array_update

            headers_count = checklist_entries_class().getHeadersCount(inclusions, exclusions)
            nested_headers_checklists.append({'label': checklist_name, 'colspan': headers_count})
            nested_headers_fields.extend(checklist_entries_class().getHeaderNames(inclusions, exclusions))
            headers_size.extend(checklist_entries_class().getHeadersSize(pixelsPerChar, inclusions, exclusions))

            headers_max_size = checklist_entries_class().getHeadersMaxSize(headers_max_size, inclusions, exclusions)

            validators = validators + checklist_entries_class().getValidators(inclusions, exclusions)

            # Get field metadata for this checklist
            checklist_model = checklist_entries_class
            for field in checklist_model._meta.get_fields():
                if hasattr(field, 'name') and hasattr(field, 'help_text'):
                    field_name = field.name
                    if field_name in ['id', 'sampleset', 'sample', 'sample_type']:
                        continue
                        
                    field_info = {
                        'name': field_name,
                        'label': checklist_model().fields.get(field_name, field_name),
                        'help_text': field.help_text or '',
                        'required': not field.blank if hasattr(field, 'blank') else False,
                        'max_length': getattr(field, 'max_length', None),
                        'choices': None,
                        'validator_pattern': None,
                        'checklist': checklist_name
                    }
                    
                    # Apply field overrides if they exist
                    if sample_set and sample_set.field_overrides and field_name in sample_set.field_overrides:
                        overrides = sample_set.field_overrides[field_name]
                        if 'required' in overrides:
                            field_info['required'] = overrides['required']
                    
                    # Check for choices - look for field_name_choice attribute
                    choice_attr_name = f"{field_name}_choice"
                    if hasattr(checklist_model, choice_attr_name):
                        choices = getattr(checklist_model, choice_attr_name)
                        field_info['choices'] = [{'value': c[0], 'label': c[1]} for c in choices]
                    elif hasattr(field, 'choices') and field.choices:
                        field_info['choices'] = [{'value': c[0], 'label': c[1]} for c in field.choices]
                    
                    # Check for validators
                    if hasattr(field, 'validators') and field.validators:
                        for validator in field.validators:
                            if hasattr(validator, 'regex'):
                                field_info['validator_pattern'] = validator.regex.pattern
                                break
                    
                    # Check for units (for unit fields)
                    units_attr_name = f"{field_name}_units"
                    unit_class_name = f"{checklist_class_name}_unit"
                    try:
                        unit_class = getattr(importlib.import_module("app.models"), unit_class_name)
                        if hasattr(unit_class, units_attr_name):
                            units = getattr(unit_class, units_attr_name)
                            field_info['units'] = [{'value': u[0], 'label': u[1]} for u in units]
                    except:
                        pass
                    
                    field_metadata[field_name] = field_info
            
            # get the checklist objects for this sample_set
            try:
                # Always use SAMPLE_TYPE_NORMAL for checklist entries since they're only created for normal samples
                checklist_sample_type = SAMPLE_TYPE_NORMAL if sample_type in [SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG] else sample_type
                checklist_entries = checklist_entries_class.objects.filter(sampleset=sample_set, sample_type=checklist_sample_type) 
                checklist_entries_list.append(checklist_entries)
            except:
                pass
        samples_headers = samples_headers + f"]"

        samples_data = []

        # Get the actual data for the sample
        for sample in samples:
            output = {}
            fields = sample.getFields(inclusions, exclusions)
            output.update(fields)

            # get the actual data for the checklists for this sample    
            for checklist_type in checklist_entries_list:
                # Always use SAMPLE_TYPE_NORMAL for checklist entries since they're only created for normal samples
                checklist_sample_type = SAMPLE_TYPE_NORMAL if sample_type in [SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG] else sample_type
                for checklist in checklist_type.all().filter(sampleset=sample_set, sample=sample, sample_type=checklist_sample_type):
                    fields = checklist.getFields(inclusions, exclusions)
                    output.update(fields)    

            samples_data.append(output)
        
        # If there are no samples yet, create an empty row for data entry
        if not samples_data and sample_set and sample_set.checklists:
            # Create an empty data structure with default values
            empty_row = {}
            
            # Add empty fields from Sample model
            sample_instance = Sample()
            sample_fields = sample_instance.getFields(inclusions, exclusions)
            for field_name in sample_fields:
                empty_row[field_name] = ''
            
            # Add empty fields from each checklist
            for checklist_name in sample_set.checklists:
                if checklist_name in Sampleset.checklist_structure:
                    checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
                    checklist_class = getattr(importlib.import_module("app.models"), checklist_class_name)
                    checklist_instance = checklist_class()
                    checklist_fields = checklist_instance.getFields(inclusions, exclusions)
                    for field_name in checklist_fields:
                        empty_row[field_name] = ''
            
            samples_data.append(empty_row)

        status_choices = [choice[1] for choice in STATUS_CHOICES]

        nested_headers.append(nested_headers_checklists)
        nested_headers.append(nested_headers_fields)

        print(f"Sending samples_data to template: {samples_data}")

        return render(request, 'samples.html', {
                'order': order,
                'samples_headers': samples_headers,
                'samples_data': samples_data,
                'sample_headers_array': sample_headers_array,
                'status_choices': status_choices,
                'project_id': project_id,
                'validators': validators,
                'nested_headers': nested_headers,
                'headers_max_size': headers_max_size,
                'headers_size': headers_size,
                'sample_type': sample_type,
                'field_metadata': json.dumps(field_metadata),
                'from_admin': from_admin,
            })
    else:
        return redirect('login')


    # for sample, plus each checklist, get set of field groups, long with the number of (selected) fields in each group as a list. 
    # Also change the fieldnames to only show the element name ie. no checklist name. 
    # Also, need to get length of longest field name in each group. 
    # And length of longest group name.

    # for sample, plus each checklist, use checklist name, plus number of field groups to construct top line - append to list
    # for sample, plus each checklist, use checklist name, plus number of fields in each group to construct second line - append to list
    # for sample, plus each checklist, get length of longest checklist name
    # take the longest number of checklist name, fieldgroup name, field name an use this to send column width

    # initially, ignore field groups, as these are not captured in the current data model.
    # for sample, plus each checklist, change the fieldnames to only show the element name ie. no checklist name
    # should get max length, and number of selected fields

    # for sample, plus each checklist, use checklist name, plus number of fields in each checklist to construct top line - append to list
    # take the longest number of checklist name, and field name an use this to send column width


def test_submg(request):
    if request.user.is_authenticated and request.user.is_staff:
        # Test endpoint - staff users only
        id = 5  # Default to 48 for backwards compatibility
        returncode = 0
        
        try:
            result = process_submg_result_inner(returncode, id)
            messages.success(request, f'SubMG result processed successfully for ID {id}')
        except Exception as e:
            messages.error(request, f'Error processing SubMG result: {str(e)}')
            logger.error(f'Test SubMG endpoint error: {str(e)}')

        return redirect('project_list')   
    else:
        raise Http404("Not found")

def test_mag(request):
    if request.user.is_authenticated and request.user.is_staff:
        # Test endpoint - staff users only
        id = 71  # Default to 61 for backwards compatibility
        returncode = 0
        
        try:
            result = process_mag_result_inner(returncode, id)
            messages.success(request, f'MAG result processed successfully for ID {id}')
        except Exception as e:
            messages.error(request, f'Error processing MAG result: {str(e)}')
            logger.error(f'Test MAG endpoint error: {str(e)}')

        return redirect('project_list')   
    else:
        raise Http404("Not found")
      
@require_POST
def advance_order_status(request, order_id):
    """
    API endpoint to advance order status to the next stage
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
    
    try:
        # Get the order and verify ownership
        order = get_object_or_404(Order, pk=order_id, project__user=request.user)
        
        # Parse the request body
        data = json.loads(request.body)
        new_status = data.get('new_status')
        
        # Validate the new status
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        # Update the order status
        old_status = order.status
        order.status = new_status
        order.status_notes = f"Status changed from {old_status} to {new_status} by {request.user.username}"
        order.save()
        
        # Log the status change
        logger.info(f"Order {order_id} status changed from {old_status} to {new_status} by user {request.user.id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Status updated successfully',
            'new_status': new_status,
            'status_display': order.get_status_display()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An error occurred'}, status=500)







    