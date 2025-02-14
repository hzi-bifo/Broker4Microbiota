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
from .forms import OrderForm, SampleForm, SamplesetForm, ProjectForm
from .models import Order, Sample, Sampleset, Project, STATUS_CHOICES
from json.decoder import JSONDecodeError
import importlib

logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('project_list')
        else:
            return render(request, 'login.html', {'form': form})
    else:
        if request.user.is_authenticated:
            return redirect('project_list')
        else:
            form = AuthenticationForm()
            return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('project_list')
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
        # Add project_id to the context
        context = super().get_context_data(**kwargs)
        context['project_id'] = self.kwargs['project_id']
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

                return redirect('order_list', project_id=project_id)

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
                return redirect('order_list', project_id=project_id)
            
        return render(request, 'metadata.html', {'sample_set': sample_set, 'project_id': project_id})
    else:
        return redirect('login')

def samples_view(request, project_id, order_id):

    if request.user.is_authenticated:
        project = get_object_or_404(Project, pk=project_id, user=request.user)

        order = get_object_or_404(Order, pk=order_id, project=project)

        if request.method == 'POST':
            sample_data = json.loads(request.POST.get('sample_data'))

            print(f"Received sample_data: {sample_data}")

            # should only be one
            sample_set = order.sampleset_set.first()

            checklists = sample_set.checklists
        
            # Delete all existing checklists for the order
            for checklist in checklists:
                checklist_name = checklist
                checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  
                checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
                checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
                
                try:
                    checklist_item_class.objects.filter(sampleset=sample_set).delete()
                except:
                    pass

            # Delete all existing samples for the order
            try:
                Sample.objects.filter(order=order).delete()
            except: 
                pass
            
            # Create new samples based on the received data
            for sample_info in sample_data:

                sample=Sample(order = order)
                sample.setFieldsFromResponse(sample_info)
                sample.sampleset = sample_set
                sample.save()

                # create new checklists based on the received data
                for checklist in checklists:
                    checklist_name = checklist
                    checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  
                    checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
                    checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
                    checklist_item_instance = checklist_item_class(sampleset = sample_set, sample = sample)
                    checklist_item_instance.setFieldsFromResponse(sample_info)
                    checklist_item_instance.save()

                print(f"Processing sample {sample.id}")

                # print(sample.getAttributes(inclusions, exclusions))

            return JsonResponse({'success': True})

        samples = order.sample_set.all().order_by('sample_id')

        print(f"Retrieved samples: {list(samples)}")

        # should only be one
        sample_set = order.sampleset_set.first()

        checklists = sample_set.checklists

        inclusions = []
        exclusions = []

        # construct headers and array (to pass data back in POST) for HoT, for samples
        samples_headers = f"[\n"
        sample_headers_array = ""
        index = 2 # make space for delete button and unsaved indicator

        samples_headers = samples_headers + f"{{ title: 'Delete', renderer: deleteButtonRenderer }},\n{{ title: 'Unsaved', data: 'unsaved', readOnly: true }},\n"
        sample_headers_array = sample_headers_array + f"Delete: row[1],\nunsaved: row[1],\n"

        sample=Sample(order = order)

        samples_headers = samples_headers + sample.getHeaders(inclusions, exclusions)
        (index, sample_headers_array_update) = sample.getHeadersArray(index, inclusions, exclusions)
        sample_headers_array = sample_headers_array + sample_headers_array_update

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

            # get the checklist objects for this sample_set
            try:
                checklist_entries = checklist_entries_class.objects.filter(sampleset=sample_set) 
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
                for checklist in checklist_type.all().filter(sampleset=sample_set, sample=sample):
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
                'project_id': project_id,
            })
    else:
        return redirect('login')














    