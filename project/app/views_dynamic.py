"""
Dynamic form views demonstrating how to use the dynamic form system
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import FormTemplate, FormSubmission, Project
from .dynamic_forms import DynamicFormBuilder


@login_required
def dynamic_project_form(request, template_id=None):
    """
    Example view showing how to use dynamic forms for project creation
    """
    # Get facility name from user profile or settings (customize as needed)
    facility_name = getattr(request.user, 'facility_name', None)
    
    try:
        if template_id:
            # Load specific template
            template = get_object_or_404(FormTemplate, id=template_id, is_active=True)
            builder = DynamicFormBuilder(form_template=template)
        else:
            # Load default project form
            builder = DynamicFormBuilder.load_from_template(
                form_type='project',
                facility_name=facility_name
            )
    except ValueError as e:
        # Fallback to file if no template in database
        try:
            builder = DynamicFormBuilder.load_from_file('project_form_default.json')
        except:
            messages.error(request, "No project form template available.")
            return redirect('project_list')
    
    if request.method == 'POST':
        form = builder.build_form(data=request.POST, files=request.FILES)
        
        if form.is_valid():
            # Create the project from form data
            project_data = form.cleaned_data
            project = Project(
                user=request.user,
                title=project_data.get('title'),
                alias=project_data.get('alias'),
                description=project_data.get('description'),
                submitted=project_data.get('submitted', False),
                study_accession_id=project_data.get('study_accession_id', ''),
                alternative_accession_id=project_data.get('alternative_accession_id', '')
            )
            project.save()
            
            # Save form submission record
            form.save_submission(
                user=request.user,
                project=project
            )
            
            messages.success(request, f'Project "{project.title}" created successfully!')
            return redirect('project_list')
    else:
        form = builder.build_form()
    
    # Get form metadata for template
    context = {
        'form': form,
        'form_title': form.form_schema.get('form_title', 'Create Project'),
        'form_description': form.form_schema.get('form_description', ''),
        'sections': form.get_sections(),
        'form_actions': form.get_form_actions(),
        'is_dynamic': True,
    }
    
    return render(request, 'dynamic_form.html', context)


@login_required
def dynamic_order_form(request, project_id, template_id=None):
    """
    Example view showing how to use dynamic forms for order creation
    """
    project = get_object_or_404(Project, pk=project_id, user=request.user)
    facility_name = getattr(request.user, 'facility_name', None)
    
    try:
        if template_id:
            # Load specific template
            template = get_object_or_404(FormTemplate, id=template_id, is_active=True)
            builder = DynamicFormBuilder(form_template=template)
        else:
            # Load default order form
            builder = DynamicFormBuilder.load_from_template(
                form_type='order',
                facility_name=facility_name
            )
    except ValueError as e:
        # Fallback to file if no template in database
        try:
            builder = DynamicFormBuilder.load_from_file('order_form_default.json')
        except:
            messages.error(request, "No order form template available.")
            return redirect('order_list', project_id=project_id)
    
    if request.method == 'POST':
        form = builder.build_form(data=request.POST, files=request.FILES)
        
        if form.is_valid():
            # Create the order from form data
            from .models import Order
            order_data = form.cleaned_data
            
            # Map form fields to model fields
            order = Order(
                project=project,
                name=order_data.get('name'),
                billing_address=order_data.get('billing_address'),
                ag_and_hzi=order_data.get('ag_and_hzi'),
                date=order_data.get('date'),
                quote_no=order_data.get('quote_no', ''),
                contact_phone=order_data.get('contact_phone'),
                email=order_data.get('email'),
                data_delivery=order_data.get('data_delivery'),
                signature=order_data.get('signature'),
                experiment_title=order_data.get('experiment_title'),
                dna=order_data.get('dna', ''),
                rna=order_data.get('rna', ''),
                library=order_data.get('library'),
                method=order_data.get('method'),
                buffer=order_data.get('buffer', ''),
                organism=order_data.get('organism'),
                isolated_from=order_data.get('isolated_from'),
                isolation_method=order_data.get('isolation_method'),
                # Optional fields
                platform=order_data.get('platform', ''),
                insert_size=order_data.get('insert_size', ''),
                library_name=order_data.get('library_name', ''),
                library_source=order_data.get('library_source', ''),
                library_selection=order_data.get('library_selection', ''),
                library_strategy=order_data.get('library_strategy', ''),
                sequencing_instrument=order_data.get('sequencing_instrument', ''),
            )
            order.save()
            
            # Save form submission record
            form.save_submission(
                user=request.user,
                order=order
            )
            
            messages.success(request, f'Order #{order.id} created successfully!')
            return redirect('order_list', project_id=project_id)
    else:
        form = builder.build_form()
    
    # Get form metadata for template
    context = {
        'form': form,
        'form_title': form.form_schema.get('form_title', 'Create Order'),
        'form_description': form.form_schema.get('form_description', ''),
        'sections': form.get_sections(),
        'form_actions': form.get_form_actions(),
        'project': project,
        'project_id': project_id,
        'is_dynamic': True,
    }
    
    return render(request, 'dynamic_form.html', context)


@login_required
def list_form_templates(request):
    """
    View to list available form templates
    """
    templates = FormTemplate.objects.filter(is_active=True).order_by('form_type', '-version')
    
    context = {
        'templates': templates,
        'form_types': dict(FormTemplate.FORM_TYPE_CHOICES),
    }
    
    return render(request, 'form_templates_list.html', context)


@login_required
def preview_form_template(request, template_id):
    """
    Preview a form template without submitting
    """
    template = get_object_or_404(FormTemplate, id=template_id)
    builder = DynamicFormBuilder(form_template=template)
    form = builder.build_form()
    
    context = {
        'form': form,
        'form_title': form.form_schema.get('form_title', 'Form Preview'),
        'form_description': form.form_schema.get('form_description', ''),
        'sections': form.get_sections(),
        'form_actions': [],  # No actions in preview mode
        'is_preview': True,
        'template': template,
    }
    
    return render(request, 'dynamic_form.html', context)


@login_required
def get_form_field_data(request):
    """
    AJAX endpoint to get form field metadata for conditional logic
    """
    form_type = request.GET.get('form_type')
    template_id = request.GET.get('template_id')
    
    if template_id:
        template = get_object_or_404(FormTemplate, id=template_id)
        schema = template.json_schema
    else:
        try:
            builder = DynamicFormBuilder.load_from_template(form_type=form_type)
            schema = builder.schema
        except:
            return JsonResponse({'error': 'No template found'}, status=404)
    
    # Extract field data for conditional logic
    fields = {}
    for section in schema.get('sections', []):
        for field in section.get('fields', []):
            fields[field['field_name']] = {
                'type': field.get('field_type'),
                'label': field.get('label'),
                'options': field.get('options', []),
            }
    
    return JsonResponse({'fields': fields})


# Utility function to migrate existing forms to dynamic system
def migrate_to_dynamic_forms():
    """
    Utility function to help migrate existing forms to the dynamic system
    This would typically be run as a management command
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Get or create system user
    system_user = User.objects.filter(username='system').first()
    if not system_user:
        system_user = User.objects.create_user(
            username='system',
            email='system@example.com',
            is_active=False
        )
    
    # Check if default templates exist
    project_template = FormTemplate.objects.filter(
        form_type='project',
        facility_specific=False,
        version='1.0'
    ).first()
    
    if not project_template:
        # Load from file
        try:
            builder = DynamicFormBuilder.load_from_file('project_form_default.json')
            FormTemplate.objects.create(
                name='Default Project Form',
                form_type='project',
                description='Default form for creating projects',
                version='1.0',
                is_active=True,
                facility_specific=False,
                json_schema=builder.schema,
                created_by=system_user
            )
            print("Created default project form template")
        except Exception as e:
            print(f"Error creating project template: {e}")
    
    # Similar for order forms...
    order_template = FormTemplate.objects.filter(
        form_type='order',
        facility_specific=False,
        version='1.0'
    ).first()
    
    if not order_template:
        try:
            builder = DynamicFormBuilder.load_from_file('order_form_default.json')
            FormTemplate.objects.create(
                name='Default Order Form',
                form_type='order',
                description='Default form for creating orders',
                version='1.0',
                is_active=True,
                facility_specific=False,
                json_schema=builder.schema,
                created_by=system_user
            )
            print("Created default order form template")
        except Exception as e:
            print(f"Error creating order template: {e}")