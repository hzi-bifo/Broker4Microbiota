from django import forms
from .models import Order, Sample

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        exclude = ['user']

class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        exclude = ['order']