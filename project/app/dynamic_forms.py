"""
Dynamic Form Builder
Generates Django forms from JSON schema definitions
"""
import json
from django import forms
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator
from django.forms import widgets
from jsonschema import validate, ValidationError as JsonValidationError
from .models import FormTemplate
import os
from django.conf import settings


class DynamicFormBuilder:
    """
    Builds Django forms dynamically from JSON schema definitions
    """
    
    # Field type mapping from JSON to Django form fields
    FIELD_TYPE_MAPPING = {
        'text': forms.CharField,
        'email': forms.EmailField,
        'phone': forms.CharField,
        'number': forms.IntegerField,
        'float': forms.FloatField,
        'date': forms.DateField,
        'datetime': forms.DateTimeField,
        'textarea': forms.CharField,
        'select': forms.ChoiceField,
        'multiselect': forms.MultipleChoiceField,
        'checkbox': forms.BooleanField,
        'radio': forms.ChoiceField,
        'file': forms.FileField,
        'hidden': forms.CharField,
        'password': forms.CharField,
        'url': forms.URLField,
        'color': forms.CharField,
    }
    
    # Widget mapping for special field types
    WIDGET_MAPPING = {
        'textarea': forms.Textarea,
        'password': forms.PasswordInput,
        'hidden': forms.HiddenInput,
        'radio': forms.RadioSelect,
        'multiselect': forms.CheckboxSelectMultiple,
        'date': forms.DateInput,
        'datetime': forms.DateTimeInput,
        'color': forms.TextInput,
    }
    
    def __init__(self, json_schema=None, form_template=None):
        """
        Initialize the form builder with either a JSON schema dict or a FormTemplate instance
        """
        if form_template:
            self.schema = form_template.get_form_definition()
            self.form_template = form_template
        elif json_schema:
            self.schema = json_schema
            self.form_template = None
        else:
            raise ValueError("Either json_schema or form_template must be provided")
    
    def build_form(self, data=None, files=None, initial=None, instance=None):
        """
        Build and return a Django Form class based on the JSON schema
        """
        # Create form attributes dict
        attrs = {
            'form_schema': self.schema,
            'form_template': self.form_template,
        }
        
        # Process each section
        for section in self.schema.get('sections', []):
            for field_def in section.get('fields', []):
                field_name = field_def['field_name']
                field = self._create_field(field_def)
                attrs[field_name] = field
        
        # Create the form class dynamically
        form_class = type(
            f"Dynamic{self.schema.get('form_type', 'Custom')}Form",
            (DynamicForm,),
            attrs
        )
        
        # Return an instance of the form
        return form_class(data=data, files=files, initial=initial)
    
    def _create_field(self, field_def):
        """
        Create a Django form field from a field definition
        """
        field_type = field_def.get('field_type', 'text')
        field_class = self.FIELD_TYPE_MAPPING.get(field_type, forms.CharField)
        
        # Build field kwargs
        kwargs = {
            'label': field_def.get('label', ''),
            'required': field_def.get('required', False),
            'help_text': field_def.get('help_text', ''),
            'initial': field_def.get('default'),
        }
        
        # Add widget if needed
        if field_type in self.WIDGET_MAPPING:
            widget_class = self.WIDGET_MAPPING[field_type]
            widget_attrs = {'class': 'form-control'}
            
            # Add placeholder
            if 'placeholder' in field_def:
                widget_attrs['placeholder'] = field_def['placeholder']
            
            # Add readonly
            if field_def.get('readonly', False):
                widget_attrs['readonly'] = True
            
            # Special handling for specific widgets
            if field_type == 'textarea' and 'rows' in field_def:
                widget_attrs['rows'] = field_def['rows']
            elif field_type == 'date':
                widget_attrs['type'] = 'date'
            elif field_type == 'datetime':
                widget_attrs['type'] = 'datetime-local'
            elif field_type == 'color':
                widget_attrs['type'] = 'color'
            
            kwargs['widget'] = widget_class(attrs=widget_attrs)
        else:
            # Default widget attributes
            kwargs['widget'] = field_class.widget(attrs={
                'class': 'form-control',
                'placeholder': field_def.get('placeholder', '')
            })
        
        # Handle choices for select/radio fields
        if field_type in ['select', 'multiselect', 'radio'] and 'options' in field_def:
            kwargs['choices'] = [
                (opt['value'], opt['label']) 
                for opt in field_def['options']
            ]
        
        # Add validators
        validators = []
        validation = field_def.get('validation', {})
        
        if 'pattern' in validation:
            validators.append(RegexValidator(
                regex=validation['pattern'],
                message=f"Please enter a valid {field_def.get('label', 'value')}"
            ))
        
        if 'min_length' in validation:
            validators.append(MinLengthValidator(validation['min_length']))
        
        if 'max_length' in validation:
            validators.append(MaxLengthValidator(validation['max_length']))
            kwargs['max_length'] = validation['max_length']
        
        if validators:
            kwargs['validators'] = validators
        
        # Handle min/max for number fields
        if field_type == 'number' and 'validation' in field_def:
            if 'min' in validation:
                kwargs['min_value'] = validation['min']
            if 'max' in validation:
                kwargs['max_value'] = validation['max']
        
        # Create and return the field
        return field_class(**kwargs)
    
    @classmethod
    def load_from_file(cls, filename):
        """
        Load a form definition from a JSON file
        """
        filepath = os.path.join(
            settings.BASE_DIR,
            'app',
            'form_templates',
            filename
        )
        
        with open(filepath, 'r') as f:
            json_schema = json.load(f)
        
        return cls(json_schema=json_schema)
    
    @classmethod
    def load_from_template(cls, form_type, facility_name=None, version=None):
        """
        Load a form definition from the database
        """
        query = FormTemplate.objects.filter(
            form_type=form_type,
            is_active=True
        )
        
        if facility_name:
            # Try facility-specific first
            facility_query = query.filter(
                facility_specific=True,
                facility_name=facility_name
            )
            if version:
                facility_query = facility_query.filter(version=version)
            
            template = facility_query.order_by('-version').first()
            if template:
                return cls(form_template=template)
        
        # Fall back to default
        query = query.filter(facility_specific=False)
        if version:
            query = query.filter(version=version)
        
        template = query.order_by('-version').first()
        if template:
            return cls(form_template=template)
        
        raise ValueError(f"No active form template found for type: {form_type}")


class DynamicForm(forms.Form):
    """
    Base class for dynamically generated forms
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply any conditional visibility rules
        if hasattr(self, 'form_schema'):
            self._apply_conditional_rules()
    
    def _apply_conditional_rules(self):
        """
        Apply conditional visibility rules based on form schema
        """
        # This would be implemented with JavaScript in the template
        # Here we can set initial visibility states
        pass
    
    def get_sections(self):
        """
        Get form sections for template rendering
        """
        if not hasattr(self, 'form_schema'):
            return []
        
        sections = []
        for section_def in self.form_schema.get('sections', []):
            section = {
                'id': section_def.get('section_id'),
                'title': section_def.get('title'),
                'icon': section_def.get('icon'),
                'collapsible': section_def.get('collapsible', False),
                'collapsed_by_default': section_def.get('collapsed_by_default', False),
                'fields': []
            }
            
            for field_def in section_def.get('fields', []):
                field_name = field_def['field_name']
                if field_name in self.fields:
                    field_info = {
                        'name': field_name,
                        'field': self[field_name],
                        'expandable_help': field_def.get('expandable_help'),
                        'show_if': field_def.get('show_if'),
                    }
                    section['fields'].append(field_info)
            
            sections.append(section)
        
        return sections
    
    def get_form_actions(self):
        """
        Get form actions for template rendering
        """
        if not hasattr(self, 'form_schema'):
            return []
        
        return self.form_schema.get('form_actions', [])
    
    def save_submission(self, user, project=None, order=None):
        """
        Save the form data as a FormSubmission
        """
        from .models import FormSubmission
        
        if not self.is_valid():
            raise ValueError("Form must be valid to save submission")
        
        submission = FormSubmission(
            form_template=getattr(self, 'form_template', None),
            user=user,
            submission_data=self.cleaned_data,
            project=project,
            order=order
        )
        submission.save()
        
        return submission


def validate_form_schema(schema):
    """
    Validate a form schema against the JSON schema
    """
    schema_path = os.path.join(
        settings.BASE_DIR,
        'app',
        'form_templates',
        'form_schema.json'
    )
    
    with open(schema_path, 'r') as f:
        form_schema = json.load(f)
    
    try:
        validate(instance=schema, schema=form_schema)
        return True, None
    except JsonValidationError as e:
        return False, str(e)