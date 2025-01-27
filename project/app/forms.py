from django import forms
from .models import Order, Sample, Sampleset, Project
from django.conf import settings
import os
import xml.etree.ElementTree as ET
import json

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = ['user']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input'}),
            'alias': forms.TextInput(attrs={'class': 'input'}),
            'description': forms.Textarea(attrs={'class': 'textarea'}),
            'study_accession_id': forms.TextInput(attrs={'class': 'input','readonly':True}),
            'alternative_accession_id': forms.TextInput(attrs={'class': 'input','readonly':True}),
        }
        help_texts = {
            'title': 'Enter the title of the project.',
            'alias': 'Enter the alias of the project.',
            'description': 'Enter a description of the project.',
            'study_accession_id': 'Enter the study accession ID, if applicable.',
            'alternative_accession_id': 'Enter the alternative accession ID, if applicable.'
        }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        exclude = ['project']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'billing_address': forms.Textarea(attrs={'class': 'textarea'}),
            'ag_and_hzi': forms.TextInput(attrs={'class': 'input'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'quote_no': forms.TextInput(attrs={'class': 'input'}),
            'contact_phone': forms.TextInput(attrs={'class': 'input'}),
            'email': forms.EmailInput(attrs={'class': 'input'}),
            'data_delivery': forms.TextInput(attrs={'class': 'input'}),
            'signature': forms.TextInput(attrs={'class': 'input'}),
            'experiment_title': forms.TextInput(attrs={'class': 'input'}),
            'dna': forms.TextInput(attrs={'class': 'input'}),
            'rna': forms.TextInput(attrs={'class': 'input'}),
            'library': forms.Select(attrs={'class': 'select'}),
            'method': forms.TextInput(attrs={'class': 'input'}),
            'buffer': forms.TextInput(attrs={'class': 'input'}),
            'organism': forms.TextInput(attrs={'class': 'input'}),
            'isolated_from': forms.TextInput(attrs={'class': 'input'}),
            'isolation_method': forms.Select(attrs={'class': 'select'}),
        }
        help_texts = {
            'name': 'Enter your full name as it appears on your billing information.',
            'billing_address': 'Provide the complete billing address for invoicing purposes.',
            'ag_and_hzi': 'Enter the AG and HZI information, if applicable.',
            'date': 'Enter the date of the order.',
            'quote_no': 'Enter the quote number, if applicable.',
            'contact_phone': 'Enter your contact phone number.',
            'email': 'Enter your email address.',
            'data_delivery': 'Enter the data delivery method.',
            'signature': 'Enter your signature.',
            'experiment_title': 'Enter the title of the experiment.',
            'dna': 'Enter the DNA information.',
            'rna': 'Enter the RNA information.',
            'library': 'Select the library type.',
            'method': 'Enter the method used.',
            'buffer': 'Enter the buffer information.',
            'organism': 'Enter the organism information.',
            'isolated_from': 'Enter the isolated from information.',
            'isolation_method': 'Select the isolation method.'
        }

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

class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        exclude = ['order']


class CreateGZForm(forms.Form):
    compression_level = forms.IntegerField(min_value=1, max_value=9, initial=9, help_text="Enter the compression level (1-9).")