from django import forms
from .models import Order, Sample, Sampleset
from django.conf import settings
import os
import xml.etree.ElementTree as ET
import json

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
            'study_accession_id': forms.TextInput(attrs={'class': 'input'}),
            # Add widgets for other fields as needed
        }
        help_texts = {
            'name': 'Enter your full name as it appears on your billing information.',
            'billing_address': 'Provide the complete billing address for invoicing purposes.',
            'ag_and_hzi': 'Enter the AG and HZI information, if applicable.',
            'study_accession_id': 'Enter the study accession ID, if applicable.',
            # Add help texts for other fields as needed
        }

class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        exclude = ['order']

class SamplesetForm(forms.ModelForm):
    class Meta:
        model = Sampleset
        exclude = ['order']

        # self.fields['checklists'] = json.loads('[]')
        # self.fields['include'] = json.loads('[]')
        # self.fields['exclude'] = json.loads('[]')
        # self.fields['custom'] = json.loads('[]')
 

        # self.fields['checklists'] = forms.ModelMultipleChoiceField(
        #     queryset=Checklist.objects.all(),
        #     widget=forms.CheckboxSelectMultiple(),
        #     required=False
        # )
        # self.fields['include'] = forms.CharField(  # A hidden field for the include field
        #     widget=forms.HiddenInput(),
        #     required=False
        # )
        # self.fields['exclude'] = forms.CharField(  # A hidden field for the exclude field
        #     widget=forms.HiddenInput(),
        #     required=False
        # )
        # self.fields['custom'] = forms.CharField(  # A hidden field for the custom field          
        #     widget=forms.HiddenInput(),
        #     required=False
        # )


class CreateGZForm(forms.Form):
    compression_level = forms.IntegerField(min_value=1, max_value=9, initial=9, help_text="Enter the compression level (1-9).")