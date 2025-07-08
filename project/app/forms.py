from django import forms
from .models import Order, Sample, Sampleset, Project, StatusNote
from django.conf import settings
import os
import xml.etree.ElementTree as ET
import json

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = ['user']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'e.g., Gut Microbiome Study 2024'
            }),
            'alias': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'e.g., GUT-2024-001'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea',
                'placeholder': 'Provide a detailed description of your study objectives, sample types, and experimental design...',
                'rows': 4
            }),
            'study_accession_id': forms.TextInput(attrs={
                'class': 'input',
                'readonly': True,
                'placeholder': 'Will be assigned after ENA submission'
            }),
            'alternative_accession_id': forms.TextInput(attrs={
                'class': 'input',
                'readonly': True,
                'placeholder': 'Optional alternative ID'
            }),
            'submitted': forms.CheckboxInput(attrs={'class': 'checkbox'}),
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
        exclude = ['project', 'status', 'status_updated_at', 'status_notes', 'submitted']
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
            'platform': forms.TextInput(attrs={'class': 'input'}),
            'insert_size': forms.TextInput(attrs={'class': 'input'}),
            'library_name': forms.TextInput(attrs={'class': 'input'}),
            'library_source': forms.TextInput(attrs={'class': 'input'}),
            'library_selection': forms.TextInput(attrs={'class': 'input'}),
            'library_strategy': forms.TextInput(attrs={'class': 'input'}),
            'sequencing_instrument': forms.TextInput(attrs={'class': 'input'}),
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
            'isolation_method': 'Select the isolation method.',
            'platform': 'Enter the sequencing platform to be used.',
            'insert_size': 'Enter the expected insert size for paired-end sequencing.',
            'library_name': 'Enter the name identifier for the sequencing library.',
            'library_source': 'Enter the source material for library construction.',
            'library_selection': 'Enter the method used for library selection.',
            'library_strategy': 'Enter the overall sequencing strategy.',
            'sequencing_instrument': 'Enter the specific sequencing instrument model.'
        }

class SamplesetForm(forms.ModelForm):
    class Meta:
        model = Sampleset
        exclude = ['order', 'sample_type']

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


# Admin forms for order management
class StatusUpdateForm(forms.ModelForm):
    """Form for updating order status with optional note"""
    status_note = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Optional note about this status change"
    )
    
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show valid next statuses if order exists
        if self.instance and self.instance.pk:
            current_status = self.instance.status
            next_status = self.instance.get_next_status()
            if next_status:
                # Allow progression to next status or any status for admin
                self.fields['status'].help_text = f"Current: {self.instance.get_status_display()}"


class OrderNoteForm(forms.ModelForm):
    """Form for adding notes to orders"""
    class Meta:
        model = StatusNote
        fields = ['note_type', 'content']
        widgets = {
            'note_type': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 4, 'class': 'textarea'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit note type choices for regular notes
        self.fields['note_type'].choices = [
            ('internal', 'Internal Note'),
            ('user_visible', 'User Visible Note'),
        ]
        self.fields['content'].label = "Note Content"


class OrderRejectionForm(forms.Form):
    """Form for rejecting an order with feedback"""
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'textarea'}),
        required=True,
        label="Reason for Rejection",
        help_text="This message will be visible to the user. Please provide clear instructions on what needs to be corrected."
    )
    new_status = forms.ChoiceField(
        choices=[('draft', 'Draft')],
        initial='draft',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Set Status To",
        help_text="Status to set the order to after rejection"
    )