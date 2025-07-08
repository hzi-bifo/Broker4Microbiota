# Dynamic Form System Documentation

## Overview

The Dynamic Form System allows different sequencing facilities to customize their forms without modifying code. Forms are defined using JSON schemas and can be loaded into the database or used directly from files.

## Features

- **JSON-based form definitions** - Define forms using simple JSON structure
- **Facility-specific forms** - Different facilities can have custom forms
- **Form versioning** - Track changes to forms over time
- **Conditional fields** - Show/hide fields based on other field values
- **Expandable help** - Rich help content for complex fields
- **Admin interface** - Manage form templates through Django admin
- **Form preview** - Preview forms before deployment
- **Import/export** - Share form templates between facilities

## Quick Start

### 1. Load Default Form Templates

```bash
python manage.py load_form_templates
```

This loads all JSON files from the `app/form_templates/` directory into the database.

### 2. Load Specific Template

```bash
python manage.py load_form_templates --file project_form_default.json
```

### 3. Validate Templates

```bash
python manage.py load_form_templates --validate-only
```

### 4. Export Templates

```bash
python manage.py export_form_templates --output-dir exports/
```

## Form Definition Structure

### Basic Structure

```json
{
  "form_id": "unique_form_id",
  "form_type": "project|order|sample|custom",
  "form_title": "Display Title",
  "form_description": "Form description",
  "version": "1.0",
  "sections": [...],
  "form_actions": [...]
}
```

### Section Structure

```json
{
  "section_id": "contact_info",
  "title": "Contact Information",
  "icon": "fa-user",
  "order": 1,
  "collapsible": false,
  "collapsed_by_default": false,
  "fields": [...]
}
```

### Field Structure

```json
{
  "field_name": "email",
  "field_type": "email",
  "label": "Email Address",
  "required": true,
  "help_text": "Your email address",
  "placeholder": "user@example.com",
  "validation": {
    "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
  },
  "expandable_help": {
    "enabled": true,
    "content": {...}
  }
}
```

## Field Types

- `text` - Single line text input
- `email` - Email input with validation
- `phone` - Phone number input
- `number` - Numeric input
- `date` - Date picker
- `datetime` - Date and time picker
- `textarea` - Multi-line text input
- `select` - Dropdown selection
- `multiselect` - Multiple selection checkboxes
- `checkbox` - Single checkbox
- `radio` - Radio button group
- `file` - File upload
- `hidden` - Hidden field
- `password` - Password input
- `url` - URL input
- `color` - Color picker

## Validation Options

```json
{
  "validation": {
    "min_length": 5,
    "max_length": 100,
    "min": 0,
    "max": 100,
    "pattern": "^[A-Z0-9]+$",
    "custom": "custom_validator_name"
  }
}
```

## Conditional Fields

Show/hide fields based on other field values:

```json
{
  "field_name": "urgency_justification",
  "field_type": "textarea",
  "show_if": {
    "field": "priority_level",
    "value": "urgent",
    "operator": "equals"
  }
}
```

Operators: `equals`, `not_equals`, `contains`, `greater_than`, `less_than`

## Expandable Help

Provide rich help content for complex fields:

```json
{
  "expandable_help": {
    "enabled": true,
    "content": {
      "title": "Guidelines",
      "description": "Detailed explanation",
      "guidelines": ["Point 1", "Point 2"],
      "examples": {
        "title": "Examples:",
        "items": ["Example 1", "Example 2"]
      },
      "warnings": {
        "title": "Avoid:",
        "items": ["Bad practice 1", "Bad practice 2"]
      }
    }
  }
}
```

## Form Actions

Define buttons and links at the form level:

```json
{
  "form_actions": [
    {
      "action_id": "submit",
      "label": "Submit",
      "type": "submit",
      "style": "primary",
      "icon": "fa-check"
    },
    {
      "action_id": "clear",
      "label": "Clear Form",
      "type": "button",
      "style": "light",
      "icon": "fa-eraser",
      "action": "clearForm"
    }
  ]
}
```

## Using Dynamic Forms in Views

### Basic Usage

```python
from app.dynamic_forms import DynamicFormBuilder

# Load from database
builder = DynamicFormBuilder.load_from_template(
    form_type='project',
    facility_name='HZI'
)

# Or load from file
builder = DynamicFormBuilder.load_from_file('project_form_default.json')

# Build form
form = builder.build_form(data=request.POST)

if form.is_valid():
    # Process form data
    data = form.cleaned_data
    # Save submission
    form.save_submission(user=request.user, project=project)
```

### In Templates

```django
{% extends 'base.html' %}

{% block content %}
<form method="post">
  {% csrf_token %}
  {% for section in form.get_sections %}
    <div class="section">
      <h3>{{ section.title }}</h3>
      {% for field in section.fields %}
        {{ field.field }}
      {% endfor %}
    </div>
  {% endfor %}
  
  {% for action in form.get_form_actions %}
    {% if action.type == 'submit' %}
      <button type="submit">{{ action.label }}</button>
    {% endif %}
  {% endfor %}
</form>
{% endblock %}
```

## Creating Facility-Specific Forms

1. Copy an existing template:
   ```bash
   cp order_form_default.json order_form_facility_x.json
   ```

2. Modify the JSON:
   - Set `"facility_specific": true`
   - Set `"facility_name": "Facility X"`
   - Customize fields as needed

3. Load the template:
   ```bash
   python manage.py load_form_templates --file order_form_facility_x.json
   ```

## Admin Interface

1. Navigate to `/admin/app/formtemplate/`
2. Create or edit form templates
3. Use the JSON editor to modify form structure
4. Preview forms before activating
5. Clone existing templates for new facilities

## Best Practices

1. **Version Control** - Always increment version when making changes
2. **Validation** - Test forms thoroughly before deployment
3. **Documentation** - Document custom fields and validation rules
4. **Backup** - Export templates before major changes
5. **Naming** - Use consistent naming conventions for field names

## Troubleshooting

### Form not loading
- Check if template is active in database
- Verify JSON syntax is valid
- Ensure form_type matches expected value

### Validation errors
- Run validation command to check schema
- Check field type compatibility
- Verify regex patterns are properly escaped

### Conditional fields not working
- Ensure field names match exactly
- Check JavaScript console for errors
- Verify operator is supported

## Migration from Static Forms

To migrate existing static forms:

1. Export current form structure to JSON
2. Create FormTemplate in database
3. Update views to use DynamicFormBuilder
4. Test thoroughly with existing data
5. Deploy with fallback to static forms

## Future Enhancements

- Visual form builder interface
- Field dependency management
- Custom validation functions
- Form submission workflows
- Multi-language support
- Field templates library
- A/B testing for forms
- Analytics integration