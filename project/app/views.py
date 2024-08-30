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
from .forms import OrderForm, SampleForm, SampleMetadataForm
from .models import Order, Sample, STATUS_CHOICES
from json.decoder import JSONDecodeError

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
        for order in orders:
            mixs_standards = order.sample_set.values_list('mixs_metadata_standard', flat=True).distinct()
            order.mixs_standards = [item[0] for item in MIXS_METADATA_STANDARDS if item[1] in mixs_standards]
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

         # Delete all existing samples for the order
        Sample.objects.filter(order=order).delete()

        # Create new samples based on the received data
        for sample_info in sample_data:
            sample_name = sample_info.get('sample_name')
            mixs_metadata_standard = sample_info.get('mixs_metadata_standard', '')
            alias = sample_info.get('alias')
            title = sample_info.get('title')
            taxon_id = sample_info.get('taxon_id')
            scientific_name = sample_info.get('scientific_name')
            investigation_type = sample_info.get('investigation_type')
            study_type = sample_info.get('study_type')
            platform = sample_info.get('platform')
            library_source = sample_info.get('library_source')
            concentration = sample_info.get('concentration')
            volume = sample_info.get('volume')
            ratio_260_280 = sample_info.get('ratio_260_280')
            ratio_260_230 = sample_info.get('ratio_260_230')
            comments = sample_info.get('comments')
            status = sample_info.get('status', '')
            mixs_metadata = sample_info.get('mixs_metadata') or ''
            try:
                mixs_metadata_json = json.loads(mixs_metadata)
            except:
                mixs_metadata_json = ''
                           
            filename_forward = sample_info.get('filename_forward')
            filename_reverse = sample_info.get('filename_reverse')
            nf_core_mag_outdir = sample_info.get('nf_core_mag_outdir')

            print(f"Processing sample {sample_name} with alias: {alias}, title: {title}, taxon_id: {taxon_id}, scientific_name: {scientific_name}, investigation_type: {investigation_type}, study_type: {study_type}, platform: {platform}, library_source: {library_source}")

            try:
                mixs_metadata = json.loads(json.dumps(mixs_metadata_json))
            except Exception as e:
                mixs_metadata = ''

            sample = Sample(
                order=order,
                sample_name=sample_name,
                mixs_metadata_standard=mixs_metadata_standard,
                alias=alias,
                title=title,
                taxon_id=taxon_id,
                scientific_name=scientific_name,
                investigation_type=investigation_type,
                study_type=study_type,
                platform=platform,
                library_source=library_source,
                concentration=concentration,
                volume=volume,
                ratio_260_280=ratio_260_280,
                ratio_260_230=ratio_260_230,
                comments=comments,
                status=status,
                mixs_metadata = mixs_metadata,
                filename_forward = filename_forward,
                filename_reverse = filename_reverse,
                nf_core_mag_outdir = nf_core_mag_outdir
                
            )
            if status:
                sample.status = status 

            sample.save()

        return JsonResponse({'success': True})

    samples = order.sample_set.all().order_by('sample_name')
    print(f"Retrieved samples: {list(samples)}")
    samples_data = [
        {
            'sample_name': sample.sample_name or '',
            'mixs_metadata_standard': sample.mixs_metadata_standard or '',
            'alias': sample.alias or '',
            'title': sample.title or '',
            'taxon_id': sample.taxon_id or '',
            'scientific_name': sample.scientific_name or '',
            'investigation_type': sample.investigation_type or '',
            'study_type': sample.study_type or '',
            'platform': sample.platform or '',
            'library_source': sample.library_source or '',
            'concentration': sample.concentration or '',
            'volume': sample.volume or '',
            'ratio_260_280': sample.ratio_260_280 or '',
            'ratio_260_230': sample.ratio_260_230 or '',
            'comments': sample.comments or '',
            'status': sample.get_status_display() or '',
            'mixs_metadata': json.dumps(sample.mixs_metadata or ''),
            'filename_forward': sample.filename_forward or '',
            'filename_reverse': sample.filename_reverse or '',
            'nf_core_mag_outdir': sample.nf_core_mag_outdir or '',
        }
        for index, sample in enumerate(samples, start=1)
    ]
    status_choices = [choice[1] for choice in STATUS_CHOICES]

    print(f"Sending samples_data to template: {samples_data}")
    
    return render(request, 'samples.html', {
            'order': order,
            'samples': samples_data,
            'mixs_metadata_standards': MIXS_METADATA_STANDARDS,
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
            sample_name = metadata.get('sample_name')
            metadata_values = metadata.get('metadata')
            print(f"Processing metadata for sample_name: {sample_name}")
            try:
                sample = Sample.objects.get(sample_name=sample_name)
                sample.mixs_metadata = metadata_values
                sample.save()
                print(f"Updated mixs_metadata for sample_name: {sample_name}")
            except Sample.DoesNotExist:
                print(f"Sample with sample_name {sample_name} does not exist.")
                continue
        return JsonResponse({'success': True})
    else:
        initial_data = []
        
        for sample in samples:
            sample_data = {
                'sample_name': sample.sample_name,
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
        else:
            form = OrderForm()

        if request.method == 'POST':
            if order_id:
                form = OrderForm(request.POST, instance=order)
            else:
                form = OrderForm(request.POST)

            if form.is_valid():
                order = form.save(commit=False)
                order.user = request.user
                order.save()
                return redirect('order_list')

        return render(request, 'order_form.html', {'form': form})
    else:
        return redirect('login')
