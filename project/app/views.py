from django import forms
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, logout
from django.views.generic import ListView
from django.forms import CheckboxSelectMultiple, CheckboxInput, DateInput, modelformset_factory
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from .mixs_metadata_standards import MIXS_METADATA_STANDARDS
from .forms import OrderForm, SampleForm, SamplesetForm, SampleMetadataForm
from .models import Order, Sample, Sampleset, STATUS_CHOICES
from json.decoder import JSONDecodeError
import importlib

logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('order_list')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

class OrderListView(ListView):
    model = Order
    template_name = 'order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        orders = Order.objects.filter(user=self.request.user)
        return orders

def order_view(request, order_id=None):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = OrderForm(request.POST)
            if form.is_valid():
                # Process the form data and save the order
                # You can access the form data using form.cleaned_data
                # For example:
                # name = form.cleaned_data['name']
                # billing_address = form.cleaned_data['billing_address']
                # ag_and_hzi = form.cleaned_data['ag_and_hzi']
                # Create a new Order instance and save it
                order = Order(user=request.user)
                order.save()
                return redirect('order_list')
        else:
            form = OrderForm()

        return render(request, 'order_form.html', {'form': form})
    else:
        return redirect('login')

def delete_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    order.delete()

    return redirect('order_list')   

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('order_list')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def samples_view(request, order_id):
    print("Received POST request")
    order = get_object_or_404(Order, pk=order_id)

    if request.method == 'POST':
        sample_data = json.loads(request.POST.get('sample_data'))

        print(f"Received sample_data: {sample_data}")

        # should only be one at this point
        sample_sets = order.sampleset_set.all()
        sample_set = sample_sets.first()

        # this needs to be passed through properly
        checklists = sample_set.checklists

        # temporary - this needs to be passed through properly
        # checklists = ['GSC_MIxS_wastewater_sludge', 'GSC_MIxS_miscellaneous_natural_or_artificial_environment']
    
        for checklist in checklists:
            checklist_name = checklist
            checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  
            checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
            checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
            
            checklist_item_class.objects.filter(order=order).delete()

        # Delete all existing samples for the order
        Sample.objects.filter(order=order).delete()

        # Create new samples based on the received data
        for sample_info in sample_data:

            sample=Sample(order = order)
            sample.setFieldsFromResponse(sample_info)
            sample.sampleset = sample_set
            sample.save()

            # for all checklists or just ones used (initially, latter)
            for checklist in checklists:
                checklist_name = checklist
                checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  
                checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
                checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
                checklist_item_instance = checklist_item_class(sample = sample, order = order)
                checklist_item_instance.setFieldsFromResponse(sample_info)
                checklist_item_instance.save()

            print(f"Processing sample {sample.id}")

            print(sample.getAttributes(inclusions, exclusions))

        return JsonResponse({'success': True})

    samples = order.sample_set.all().order_by('sample_id')

    print(f"Retrieved samples: {list(samples)}")

    # should only be one at this point
    sample_sets = order.sampleset_set.all()
    sample_set = sample_sets.first()

    # this needs to be passed through properly
    checklists = sample_set.checklists
    # ['GSC_MIxS_wastewater_sludge', 'GSC_MIxS_miscellaneous_natural_or_artificial_environment']

    inclusions = []
    exclusions = []

    samples_headers = f"[\n"
    sample_headers_array = ""
    index = 2 # make space for delete button and unsaved indicator

    samples_headers = samples_headers + f"{{ title: 'Delete', renderer: deleteButtonRenderer }},\n{{ title: 'Unsaved', data: 'unsaved', readOnly: true }},\n"
    sample_headers_array = sample_headers_array + f"Delete: row[1],\nunsaved: row[1],\n"

    sample=Sample(order = order)
    samples_headers = samples_headers + sample.getHeaders(inclusions, exclusions)
    (index, sample_headers_array_update) = sample.getHeadersArray(index, inclusions, exclusions)
    sample_headers_array = sample_headers_array + sample_headers_array_update

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

        try:
            checklist_entries = checklist_entries_class.objects.all() # filter on order or sample
            checklist_entries_list.append(checklist_entries)
        except:
            pass
    samples_headers = samples_headers + f"]"

    samples_data = []

    for sample in samples:
        output = {}
        fields = sample.getFields(inclusions, exclusions)
        output.update(fields)

        # get the checklists for this sample    
        for checklist_type in checklist_entries_list:
            for checklist in checklist_type.all().filter(sample=sample):
                fields = checklist.getFields(inclusions, exclusions)
                output.update(fields)    

        samples_data.append(output)

    status_choices = [choice[1] for choice in STATUS_CHOICES]

    print(f"Sending samples_data to template: {samples_data}")

    return render(request, 'samples.html', {
            'order': order,
            'samples_headers': samples_headers,
            'samples_data': samples_data,
            'sample_headers_array': sample_headers_array,
            'status_choices': status_choices,
        })

    
def mixs_view(request, order_id, mixs_standard):
    print(f"Received request for order_id: {order_id} with mixs_standard: {mixs_standard}")
    order = Order.objects.get(id=order_id)

    # Find the tuple in MIXS_METADATA_STANDARDS where the first element matches mixs_standard
    mixs_metadata_standard = next((item[0] for item in MIXS_METADATA_STANDARDS if item[0] == mixs_standard), None)
    print(f"Mixs metadata standard: {mixs_metadata_standard}")

    if not mixs_metadata_standard:
        return JsonResponse({'error': 'Invalid MIXS metadata standard'}, status=400)
  
    # Convert the mixs_standard to the format with spaces for display purposes
    mixs_standard_display = next((item[1] for item in MIXS_METADATA_STANDARDS if item[0] == mixs_standard), mixs_standard)
    print(f"Mixs standard display: {mixs_standard_display}")

    # Filter the samples based on the order and mixs_metadata_standard
    samples = Sample.objects.filter(order=order, mixs_metadata_standard=mixs_standard_display)
    print(f"Found {samples.count()} samples for order_id: {order_id}")
    
    if request.method == 'POST':
        try:
            mixs_metadata = json.loads(request.body)
            print(f"Received POST data: {mixs_metadata}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        for metadata in mixs_metadata:
            sample_id = metadata.get('sample_id')
            metadata_values = metadata.get('metadata')
            print(f"Processing metadata for sample_id: {sample_id}")
            try:
                sample = Sample.objects.get(sample_id=sample_id)
                sample.mixs_metadata = metadata_values
                sample.save()
                print(f"Updated mixs_metadata for sample_id: {sample_id}")
            except Sample.DoesNotExist:
                print(f"Sample with sample_id {sample_id} does not exist.")
                continue
        return JsonResponse({'success': True})
    else:
        initial_data = []
        
        for sample in samples:
            sample_data = {
                'sample_id': sample.sample_id,
            }
            if sample.mixs_metadata:
                sample_data['mixs_metadata'] = sample.mixs_metadata
        
            initial_data.append(sample_data)
        print(f"Preparing initial data for form: {initial_data}")
        form = SampleMetadataForm(mixs_metadata_standard=mixs_metadata_standard, initial=initial_data)
    context = {
        'order': order,
        'samples': samples,
        'form': form,
        'mixs_standard': mixs_standard_display, 
    }
    return render(request, 'mixs_view.html', context)
    
def order_list_view(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'order_list.html', {'orders': orders, 'user': request.user})

def order_view(request, order_id=None):
    if request.user.is_authenticated:
        if order_id:
            order = get_object_or_404(Order, pk=order_id, user=request.user)
            form = OrderForm(instance=order)
            sample_set = Sampleset(order=order)
           
        else:
            form = OrderForm()
            sample_set = Sampleset()

        if request.method == 'POST':
            if order_id:
                form = OrderForm(request.POST, instance=order)
            else:
                form = OrderForm(request.POST)

            if form.is_valid():
                order = form.save(commit=False)
                order.user = request.user
                order.save()

                # # Create a new Sampleset instance and save it
                # sample_set = Sampleset(order=order)
                # # sample_set.checklists = form.cleaned_data['checklists']

                # # temporary
                # checklist_string = '[{"checklist_name": "GSC_MIxS_wastewater_sludge", "checklist_code" : "ERC000023"}]'

                # sample_set.checklists = json.loads(checklist_string)
                # # sample_set.checklists = json.loads('["GSC_MIxS_wastewater_sludge", "GSC_MIxS_miscellaneous_natural_or_artificial_environment"]')

                # # temporary
                # for checklist in sample_set.checklists:
                #     checklist_name = checklist['checklist_name']
                #     checklist_code = checklist['checklist_code']  
                #     unitchecklist_class_name = Sampleset.checklist_structure[checklist_name]['unitchecklist_class_name']
                #     unitchecklist_item_class =  getattr(importlib.import_module("app.models"), unitchecklist_class_name)
                #     unitchecklist_item_instance = unitchecklist_item_class(order = order)
                #     # temporary
                #     if unitchecklist_class_name == 'GSC_MIxS_wastewater_sludge_unit':
                #         unitchecklist_item_instance.GSC_MIxS_wastewater_sludge_sample_volume_or_weight_for_DNA_extraction = 'ng'                    
                #     unitchecklist_item_instance.save()

                # # temporary
                # sample_set.include = json.loads('[]')
                # sample_set.exclude = json.loads('[]')
                # sample_set.custom = json.loads('[]')

                # sample_set.save()

                # create a 

                return redirect('order_list')

        return render(request, 'order_form.html', {'form': form})
    else:
        return redirect('login')

def metadata_view(request, order_id):
    
    if request.user.is_authenticated:
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        sample_set = order.sampleset_set.first()
        if not sample_set:
            sample_set = Sampleset(order=order) 
        form = SamplesetForm(instance=sample_set)
        
        if request.method == 'POST':
            if order_id:
                form = SamplesetForm(request.POST, instance=sample_set)
            else:
                form = SamplesetForm(request.POST)

            if form.is_valid():
                sample_set = form.save(commit=False)
                sample_set.user = request.user
                # temporary
                checklist_string = '["GSC_MIxS_wastewater_sludge"]'
                sample_set.checklists = json.loads(checklist_string)
                sample_set.include = json.loads('[]')
                sample_set.exclude = json.loads('[]')
                sample_set.custom = json.loads('[]')
                sample_set.save()

                # temporary
                for checklist in sample_set.checklists:
                    checklist_name = checklist
                    checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  
                    unitchecklist_class_name = Sampleset.checklist_structure[checklist_name]['unitchecklist_class_name']
                    unitchecklist_item_class =  getattr(importlib.import_module("app.models"), unitchecklist_class_name)
                    unitchecklist_item_instance = unitchecklist_item_class(order = order)
                    # temporary
                    if unitchecklist_class_name == 'GSC_MIxS_wastewater_sludge_unit':
                        unitchecklist_item_instance.GSC_MIxS_wastewater_sludge_sample_volume_or_weight_for_DNA_extraction = 'ng'                    
                    unitchecklist_item_instance.save()

                return redirect('order_list')
            
        return render(request, 'metadata.html', {'form': form})
    else:
        return redirect('login')







    