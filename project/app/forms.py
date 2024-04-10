from django import forms
from .models import Order, Sample
from django.conf import settings
import os
import xml.etree.ElementTree as ET

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


class SampleMetadataForm(forms.Form):
    def __init__(self, *args, **kwargs):
        mixs_metadata_standard = kwargs.pop('mixs_metadata_standard', None)
        super().__init__(*args, **kwargs)

        if mixs_metadata_standard:
            xml_file = os.path.join(settings.BASE_DIR, 'static', 'xml', f'{mixs_metadata_standard}.xml')
            tree = ET.parse(xml_file)
            root = tree.getroot()

            for field in root.findall('.//FIELD'):
                label = field.find('LABEL').text
                name = field.find('NAME').text
                description = field.find('DESCRIPTION').text
                field_type = field.find('FIELD_TYPE')
                mandatory = field.find('MANDATORY').text
                multiplicity = field.find('MULTIPLICITY').text

                if field_type.find('TEXT_FIELD') is not None:
                    self.fields[name] = forms.CharField(
                        label=label,
                        required=mandatory == 'mandatory',
                        help_text=description,
                        widget=forms.TextInput(attrs={'class': 'form-control'})
                    )

class CreateGZForm(forms.Form):
    compression_level = forms.IntegerField(min_value=1, max_value=9, initial=9, help_text="Enter the compression level (1-9).")