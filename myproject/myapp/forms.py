from django import forms
from .models import Order, Sample

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        exclude = ['user']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'billing_address': forms.Textarea(attrs={'class': 'textarea'}),
            'ag_and_hzi': forms.TextInput(attrs={'class': 'input'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'contact_phone': forms.TextInput(attrs={'class': 'input'}),
            'email': forms.EmailInput(attrs={'class': 'input'}),
            'library': forms.Select(attrs={'class': 'select'}),
            'isolation_method': forms.Select(attrs={'class': 'select'}),
            # Add widgets for other fields as needed
        }
        help_texts = {
            'name': 'Enter your full name as it appears on your billing information.',
            'billing_address': 'Provide the complete billing address for invoicing purposes.',
            'ag_and_hzi': 'Enter the AG and HZI information, if applicable.',
            # Add help texts for other fields as needed
        }

class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        exclude = ['order']