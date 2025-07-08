from django import forms
import json
import logging
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
import importlib
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
        
        # Add user-visible notes for each order
        for order in context['orders']:
            # Get the latest user-visible note (especially rejections)
            latest_note = order.notes.filter(
                note_type__in=['user_visible', 'rejection']
            ).order_by('-created_at').first()
            order.latest_user_note = latest_note
        
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

            # Check for any samples for order, and abort if any found
            samples = order.sample_set.filter()
            if samples:
                return render(request, 'metadata.html', {'sample_set': sample_set, 'project_id': project_id, 'error_message': 'Cannot change metadata while samples exist'})

            if order_id:
                form = SamplesetForm(request.POST, instance=sample_set)
            else:
                form = SamplesetForm(request.POST)

            if form.is_valid():
                sample_set = form.save(commit=False)
                sample_set.user = request.user
                sample_set.save()

                # temporary
                # for checklist in sample_set.checklists:
                #     checklist_name = checklist
                #     checklist_item = Sampleset.checklist_structure[checklist_name]
                #     checklist_code = checklist_item['checklist_code']  
                #     unitchecklist_class_name = checklist_item['unitchecklist_class_name']
                #     unitchecklist_item_class =  getattr(importlib.import_module("app.models"), unitchecklist_class_name)
                #     unitchecklist_item_instance = unitchecklist_item_class(order = order)
                #     # temporary
                #     if unitchecklist_class_name == 'GSC_MIxS_wastewater_sludge_unit':
                #         unitchecklist_item_instance.GSC_MIxS_wastewater_sludge_sample_volume_or_weight_for_DNA_extraction = 'ng'                    
                #         unitchecklist_item_instance.save()

                # order.save()

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

                return redirect('order_list', project_id=project_id)
            
        return render(request, 'metadata.html', {'sample_set': sample_set, 'project_id': project_id})
    else:
        return redirect('login')

def samples_view(request, project_id, order_id, sample_type):

    if request.user.is_authenticated:
        project = get_object_or_404(Project, pk=project_id, user=request.user)

        order = get_object_or_404(Order, pk=order_id, project=project)

        if not (sample_type in [SAMPLE_TYPE_NORMAL, SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG]):
            raise Http404()

        if request.method == 'POST':
            sample_data = json.loads(request.POST.get('sample_data'))

            print(f"Received sample_data: {sample_data}")

            # should only be one
            sample_set = order.sampleset_set.filter(sample_type=sample_type).first()

            checklists = sample_set.checklists
        
            # Delete all existing checklists for the order
            for checklist in checklists:
                checklist_name = checklist
                checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  
                checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
                checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
                
                try:
                    checklist_item_class.objects.filter(sampleset=sample_set, sample_type=sample_type).delete()
                except:
                    pass

                unitchecklist_class_name = Sampleset.checklist_structure[checklist_name]['unitchecklist_class_name']
                unitchecklist_item_class =  getattr(importlib.import_module("app.models"), unitchecklist_class_name)
                
                try:
                    unitchecklist_item_class.objects.filter(sampleset=sample_set, sample_type=sample_type).delete()
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
                sample.setFieldsFromResponse(sample_info)
                sample.sampleset = sample_set
                sample.save()

                # create new checklists based on the received data
                for checklist in checklists:
                    checklist_name = checklist
                    checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  
                    checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
                    checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
                    checklist_item_instance = checklist_item_class(sampleset = sample_set, sample = sample, sample_type=sample_type)
                    checklist_item_instance.setFieldsFromResponse(sample_info)
                    checklist_item_instance.save()
                    unitchecklist_class_name = Sampleset.checklist_structure[checklist_name]['unitchecklist_class_name']
                    unitchecklist_item_class =  getattr(importlib.import_module("app.models"), unitchecklist_class_name)
                    unitchecklist_item_instance = unitchecklist_item_class(sampleset = sample_set, sample = sample, sample_type=sample_type)
                    # unitchecklist_item_instance.setFieldsFromResponse(sample_info)
                    unitchecklist_item_instance.save()

                print(f"Processing sample {sample.id}")

                # print(sample.getAttributes(inclusions, exclusions))

            return JsonResponse({'success': True})

        samples = order.sample_set.filter(sample_type=sample_type).order_by('sample_id')

        print(f"Retrieved samples: {list(samples)}")

        # should only be one
        sample_set = order.sampleset_set.filter(sample_type=sample_type).first()

        checklists = sample_set.checklists

        inclusions = []
        exclusions = []
        extra_choices = []

        if sample_type == SAMPLE_TYPE_NORMAL:
            exclusions = "assembly,bin"
            extra_choices = []
        elif sample_type == SAMPLE_TYPE_ASSEMBLY:
            exclusions = "bin_identifier"
            assemblies = Assembly.objects.filter(order=order)
            for assembly in assemblies:
                extra_choices.append(f"{assembly.id}")
        elif sample_type == SAMPLE_TYPE_BIN:
            exclusions = "assembly"
            bins = Bin.objects.filter(order=order)
            for bin in bins:
                extra_choices.append(f"{bin.id}")
        elif sample_type == SAMPLE_TYPE_MAG:
            exclusions = "assembly,bin"
            extra_choices = []

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
                checklist_entries = checklist_entries_class.objects.filter(sampleset=sample_set, sample_type=sample_type) 
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
                for checklist in checklist_type.all().filter(sampleset=sample_set, sample=sample, sample_type=sample_type):
                    fields = checklist.getFields(inclusions, exclusions)
                    output.update(fields)    

            samples_data.append(output)

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
        id = request.GET.get('id', '48')  # Default to 48 for backwards compatibility
        returncode = int(request.GET.get('returncode', '0'))
        
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
        id = request.GET.get('id', '61')  # Default to 61 for backwards compatibility
        returncode = int(request.GET.get('returncode', '0'))
        
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







    