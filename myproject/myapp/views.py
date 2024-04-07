from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, logout
from .forms import OrderForm, SampleForm
from .models import Order, Sample
from django.views.generic import ListView
from funky_sheets.formsets import HotView
from django.forms import CheckboxSelectMultiple, CheckboxInput, DateInput
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.forms import modelformset_factory
from django import forms
from django.http import JsonResponse
import json
from .mixs_metadata_standards import MIXS_METADATA_STANDARDS


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
            order.mixs_standards = order.sample_set.values_list('mixs_metadata_standard', flat=True).distinct()
        return orders

def order_view(request, order_id=None):
    if request.user.is_authenticated:
        if order_id:
            order = get_object_or_404(Order, pk=order_id, user=request.user)
        else:
            order = Order(user=request.user)

        if request.method == 'POST':
            form = OrderForm(request.POST, instance=order)
            if form.is_valid():
                order = form.save(commit=False)
                order.user = request.user
                order.save()
                return redirect('order_list')
        else:
            form = OrderForm(instance=order)

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
            index = sample_info.get('index')
            concentration = sample_info.get('concentration')
            sample_name = sample_info.get('sample_name')
            volume = sample_info.get('volume')
            ratio_260_280 = sample_info.get('ratio_260_280')
            ratio_260_230 = sample_info.get('ratio_260_230')
            comments = sample_info.get('comments')
            mixs_metadata_standard = sample_info.get('mixs_metadata_standard', '')

            print(f"Processing sample {index} with concentration {concentration}, volume {volume}, ratio_260_280 {ratio_260_280}, ratio_260_230 {ratio_260_230}, comments {comments}, mixs_metadata_standard {mixs_metadata_standard}")

            sample = Sample(
                order=order,
                sample_name=sample_name,
                concentration=concentration,
                volume=volume,
                ratio_260_280=ratio_260_280,
                ratio_260_230=ratio_260_230,
                comments=comments,
                mixs_metadata_standard=mixs_metadata_standard
            )
            sample.save()

        return JsonResponse({'success': True})


    samples = order.sample_set.all().order_by('sample_name')
    print(f"Retrieved samples: {list(samples)}")
    samples_data = [
        {
            'index': index,
            'sample_name': sample.sample_name or '',
            'mixs_metadata_standard': sample.mixs_metadata_standard or '',
            'concentration': sample.concentration or '',
            'volume': sample.volume or '',
            'ratio_260_280': sample.ratio_260_280 or '',
            'ratio_260_230': sample.ratio_260_230 or '',
            'comments': sample.comments or ''
        }
        for index, sample in enumerate(samples, start=1)
    ]
    print(f"Sending samples_data to template: {samples_data}")
    return render(request, 'samples.html', {
            'order': order,
            'samples': samples_data,
            'mixs_metadata_standards': MIXS_METADATA_STANDARDS,
        })
def mixs_view(request, order_id, mixs_standard):
    order = get_object_or_404(Order, pk=order_id)
    samples = order.sample_set.filter(mixs_metadata_standard=mixs_standard)
    return render(request, 'mixs_view.html', {'order': order, 'mixs_standard': mixs_standard, 'samples': samples})