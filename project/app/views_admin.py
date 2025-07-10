"""
Admin views for sequencing center staff to manage orders and projects
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.apps import apps
from django.views.decorators.http import require_http_methods
from collections import OrderedDict
import csv
import importlib
import os
import shutil
import hashlib
from django.conf import settings
from django.template.loader import render_to_string
from pathlib import Path

from .models import Order, Project, StatusNote, Sample, SAMPLE_TYPE_NORMAL, Sampleset, Read, ProjectSubmission
from django.contrib.auth.models import User
from .forms import StatusUpdateForm, OrderNoteForm, OrderRejectionForm, UserEditForm, UserCreateForm, TechnicalDetailsForm


@staff_member_required
def admin_dashboard(request):
    """
    Main admin dashboard showing statistics and orders needing action
    """
    # Calculate date 30 days ago
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Get statistics
    stats = {
        'total_orders': Order.objects.count(),
        'orders_last_30_days': Order.objects.filter(
            status_updated_at__gte=thirty_days_ago
        ).count(),
        'orders_needing_action': Order.objects.filter(
            status='ready_for_sequencing'
        ).count(),
        'total_projects': Project.objects.count(),
        'active_projects': Project.objects.filter(
            order__status__in=['ready_for_sequencing', 'sequencing_in_progress', 'data_processing']
        ).distinct().count(),
        'total_users': User.objects.filter(is_active=True, is_staff=False).count(),
    }
    
    # Get orders by status in workflow order
    orders_by_status = []
    status_colors = {
        'draft': 'is-light',
        'ready_for_sequencing': 'is-info',
        'sequencing_in_progress': 'is-warning',
        'sequencing_completed': 'is-primary',
        'data_processing': 'is-primary',
        'data_delivered': 'is-success',
        'completed': 'is-success is-light',
    }
    
    # Define the workflow order
    workflow_order = [
        ('draft', 'Draft'),
        ('ready_for_sequencing', 'Ready for Sequencing'),
        ('sequencing_in_progress', 'Sequencing in Progress'),
        ('sequencing_completed', 'Sequencing Completed'),
        ('data_processing', 'Data Processing'),
        ('data_delivered', 'Data Delivered'),
        ('completed', 'Completed'),
    ]
    
    total_orders = stats['total_orders'] or 1  # Avoid division by zero
    
    for status_code, status_label in workflow_order:
        count = Order.objects.filter(status=status_code).count()
        orders_by_status.append({
            'code': status_code,
            'label': status_label,
            'count': count,
            'color': status_colors.get(status_code, 'is-light'),
            'percentage': round((count / total_orders) * 100, 1)
        })
    
    stats['orders_by_status'] = orders_by_status
    
    # Get recent orders needing action
    orders_needing_action = Order.objects.filter(
        status='ready_for_sequencing'
    ).select_related('project', 'project__user').order_by('-status_updated_at')[:10]
    
    # Get recent activity (all types of notes/changes)
    recent_activity = StatusNote.objects.all().select_related(
        'order', 'order__project', 'user'
    ).order_by('-created_at')[:20]
    
    context = {
        'stats': stats,
        'orders_needing_action': orders_needing_action,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'admin_dashboard.html', context)


@staff_member_required
def admin_order_list(request):
    """
    List all orders with filtering and search capabilities
    """
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    user_search = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Start with all orders
    orders = Order.objects.select_related('project', 'project__user').all()
    
    # Apply filters
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if user_search:
        orders = orders.filter(
            Q(project__user__username__icontains=user_search) |
            Q(project__user__email__icontains=user_search) |
            Q(name__icontains=user_search)
        )
    
    if date_from:
        orders = orders.filter(date__gte=date_from)
    
    if date_to:
        orders = orders.filter(date__lte=date_to)
    
    # Order by most recent first
    orders = orders.order_by('-status_updated_at')
    
    # Pagination
    paginator = Paginator(orders, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add sample counts
    for order in page_obj:
        order.sample_count = order.get_sample_count()
    
    context = {
        'page_obj': page_obj,
        'status_choices': Order.STATUS_CHOICES,
        'current_filters': {
            'status': status_filter,
            'user': user_search,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'admin_order_list.html', context)


@staff_member_required
def admin_order_detail(request, order_id):
    """
    Detailed view of a single order with all information and actions
    """
    order = get_object_or_404(Order, id=order_id)
    
    # Get all samples for this order with read information
    samples = Sample.objects.filter(order=order, sample_type=SAMPLE_TYPE_NORMAL).prefetch_related('read_set')
    
    # Get MIxS checklist information
    sampleset = order.sampleset_set.filter(sample_type=SAMPLE_TYPE_NORMAL).first()
    selected_checklists = []
    mandatory_fields_count = 0
    selected_optional_count = 0
    total_fields_count = 0
    
    if sampleset and sampleset.checklists:
        for checklist_name in sampleset.checklists:
            if checklist_name in Sampleset.checklist_structure:
                # Get the checklist model to count total fields
                checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
                checklist_class = getattr(importlib.import_module("app.models"), checklist_class_name)
                all_fields = checklist_class._meta.get_fields()
                relevant_fields = [f for f in all_fields 
                                 if f.name not in ['id', 'sampleset', 'sample', 'sample_type']]
                total_fields_count += len(relevant_fields)
                
                # Count mandatory fields
                mandatory_count = sum(1 for f in relevant_fields 
                                    if hasattr(f, 'blank') and not f.blank)
                mandatory_fields_count += mandatory_count
                
                # Count selected optional fields for this checklist
                if sampleset.selected_fields:
                    selected_optional = sum(1 for f in relevant_fields 
                                          if hasattr(f, 'blank') and f.blank and
                                          sampleset.selected_fields.get(f.name, False))
                else:
                    # If no field selection, assume all optional fields are selected
                    selected_optional = len(relevant_fields) - mandatory_count
                
                selected_optional_count += selected_optional
                
                checklist_info = {
                    'name': checklist_name.replace('_', ' ').title(),
                    'code': Sampleset.checklist_structure[checklist_name]['checklist_code'],
                    'raw_name': checklist_name,
                    'field_count': len(relevant_fields),
                    'mandatory_count': mandatory_count,
                    'selected_optional': selected_optional
                }
                selected_checklists.append(checklist_info)
    
    # Get status history and notes
    status_history = order.get_status_history()
    all_notes = order.get_notes(include_internal=True)
    
    # Calculate read statistics
    samples_with_reads = 0
    samples_without_reads = 0
    for sample in samples:
        if sample.read_set.exists():
            samples_with_reads += 1
        else:
            samples_without_reads += 1
    
    read_completion_percentage = 0
    if samples.count() > 0:
        read_completion_percentage = int((samples_with_reads / samples.count()) * 100)
    
    # Initialize forms
    status_form = StatusUpdateForm(instance=order)
    note_form = OrderNoteForm()
    rejection_form = OrderRejectionForm()
    technical_form = TechnicalDetailsForm(instance=order)
    
    context = {
        'order': order,
        'project': order.project,
        'samples': samples,
        'sampleset': sampleset,
        'selected_checklists': selected_checklists,
        'mandatory_fields_count': mandatory_fields_count,
        'selected_optional_count': selected_optional_count,
        'total_fields_count': total_fields_count,
        'status_history': status_history,
        'all_notes': all_notes,
        'status_form': status_form,
        'note_form': note_form,
        'rejection_form': rejection_form,
        'technical_form': technical_form,
        'can_advance': order.can_advance_status(),
        'next_status': order.get_next_status(),
        'samples_with_reads': samples_with_reads,
        'samples_without_reads': samples_without_reads,
        'read_completion_percentage': read_completion_percentage,
    }
    
    return render(request, 'admin_order_detail.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_update_order_status(request, order_id):
    """
    Update order status with optional note
    """
    order = get_object_or_404(Order, id=order_id)
    form = StatusUpdateForm(request.POST, instance=order)
    
    if form.is_valid():
        new_status = form.cleaned_data['status']
        note_content = form.cleaned_data.get('status_note', '')
        
        # Add status change note
        order.add_status_note(
            user=request.user,
            new_status=new_status,
            content=note_content
        )
        
        messages.success(request, f'Order status updated to {order.get_status_display()}')
    else:
        messages.error(request, 'Error updating order status')
    
    return redirect('admin_order_detail', order_id=order_id)


@staff_member_required
@require_http_methods(["POST"])
def admin_add_order_note(request, order_id):
    """
    Add a note to an order
    """
    order = get_object_or_404(Order, id=order_id)
    form = OrderNoteForm(request.POST)
    
    if form.is_valid():
        note = form.save(commit=False)
        note.order = order
        note.user = request.user
        note.save()
        
        messages.success(request, 'Note added successfully')
    else:
        messages.error(request, 'Error adding note')
    
    return redirect('admin_order_detail', order_id=order_id)


@staff_member_required
@require_http_methods(["POST"])
def admin_reject_order(request, order_id):
    """
    Reject an order with a required feedback note
    """
    order = get_object_or_404(Order, id=order_id)
    form = OrderRejectionForm(request.POST)
    
    if form.is_valid():
        rejection_reason = form.cleaned_data['rejection_reason']
        new_status = form.cleaned_data.get('new_status', 'draft')
        
        # Reject the order with note
        order.reject_with_note(
            user=request.user,
            content=rejection_reason,
            new_status=new_status
        )
        
        messages.success(request, 'Order has been sent back for review')
    else:
        messages.error(request, 'Please provide a rejection reason')
    
    return redirect('admin_order_detail', order_id=order_id)


@staff_member_required
def admin_export_orders(request):
    """
    Export filtered orders to CSV
    """
    # Get the same filters as the list view
    status_filter = request.GET.get('status', '')
    user_search = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Start with all orders
    orders = Order.objects.select_related('project', 'project__user').all()
    
    # Apply filters
    if status_filter:
        orders = orders.filter(status=status_filter)
    if user_search:
        orders = orders.filter(
            Q(project__user__username__icontains=user_search) |
            Q(project__user__email__icontains=user_search)
        )
    if date_from:
        orders = orders.filter(date__gte=date_from)
    if date_to:
        orders = orders.filter(date__lte=date_to)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Order ID', 'Project', 'User', 'Email', 'Order Name', 
        'Status', 'Date Created', 'Last Updated', 'Sample Count',
        'Experiment Title', 'Platform', 'Library'
    ])
    
    for order in orders:
        writer.writerow([
            order.id,
            order.project.title,
            order.project.user.username,
            order.project.user.email,
            order.name,
            order.get_status_display(),
            order.date,
            order.status_updated_at,
            order.get_sample_count(),
            order.experiment_title,
            order.platform,
            order.library
        ])
    
    return response


@staff_member_required
def admin_bulk_update_status(request):
    """
    Bulk update order statuses
    """
    if request.method == 'POST':
        order_ids = request.POST.getlist('order_ids')
        new_status = request.POST.get('new_status')
        
        if order_ids and new_status:
            orders = Order.objects.filter(id__in=order_ids)
            updated_count = 0
            
            for order in orders:
                # Only update if status progression is valid
                if order.get_next_status() == new_status or new_status in dict(Order.STATUS_CHOICES):
                    order.add_status_note(
                        user=request.user,
                        new_status=new_status,
                        content=f"Bulk status update by {request.user.username}"
                    )
                    updated_count += 1
            
            messages.success(request, f'{updated_count} orders updated successfully')
        else:
            messages.error(request, 'Please select orders and a new status')
    
    return redirect('admin_order_list')


@staff_member_required
def admin_user_list(request):
    """
    List all users with ability to filter by staff/superuser status
    """
    # Get filter parameters
    user_type = request.GET.get('type', '')
    search = request.GET.get('search', '')
    
    # Start with all users
    users = User.objects.all()
    
    # Apply filters
    if user_type == 'staff':
        users = users.filter(is_staff=True)
    elif user_type == 'superuser':
        users = users.filter(is_superuser=True)
    elif user_type == 'regular':
        users = users.filter(is_staff=False)
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Order by username
    users = users.order_by('username')
    
    # Pagination
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_filters': {
            'type': user_type,
            'search': search,
        }
    }
    
    return render(request, 'admin_user_list.html', context)


@staff_member_required
def admin_user_edit(request, user_id):
    """
    Edit user details
    """
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully')
            return redirect('admin_user_list')
    else:
        form = UserEditForm(instance=user)
    
    context = {
        'form': form,
        'edited_user': user,
    }
    
    return render(request, 'admin_user_edit.html', context)


@staff_member_required
def admin_user_create(request):
    """
    Create a new user
    """
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully')
            return redirect('admin_user_list')
    else:
        form = UserCreateForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'admin_user_create.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_update_technical_details(request, order_id):
    """
    Update technical details of an order
    """
    order = get_object_or_404(Order, id=order_id)
    form = TechnicalDetailsForm(request.POST, instance=order)
    
    if form.is_valid():
        form.save()
        messages.success(request, 'Technical details updated successfully')
    else:
        messages.error(request, 'Error updating technical details')
    
    return redirect('admin_order_detail', order_id=order.id)


@staff_member_required
def admin_get_sample_fields(request, sample_id):
    """
    Get all MIxS fields for a sample as JSON
    """
    sample = get_object_or_404(Sample, id=sample_id)
    
    # Get the sampleset to find which checklists are selected
    sampleset = sample.order.sampleset_set.filter(sample_type=sample.sample_type).first()
    
    fields_data = {
        'sample_id': sample.sample_id,
        'sample_title': sample.sample_title,
        'core_fields': {},
        'checklist_fields': {}
    }
    
    # Get core sample fields
    core_field_names = ['sample_id', 'tax_id', 'scientific_name', 'sample_alias', 
                        'sample_title', 'sample_description', 'collection_date', 'organism']
    for field_name in core_field_names:
        if hasattr(sample, field_name):
            value = getattr(sample, field_name)
            if value:
                fields_data['core_fields'][field_name.replace('_', ' ').title()] = value
    
    # Add read file information
    reads = Read.objects.filter(sample=sample)
    if reads.exists():
        fields_data['read_files'] = []
        for read in reads:
            read_info = {
                'file_1': read.file_1 if read.file_1 else 'Not specified',
                'file_2': read.file_2 if read.file_2 else 'Not specified',
                'checksum_1': read.read_file_checksum_1[:8] + '...' if read.read_file_checksum_1 else 'N/A',
                'checksum_2': read.read_file_checksum_2[:8] + '...' if read.read_file_checksum_2 else 'N/A',
            }
            fields_data['read_files'].append(read_info)
    
    # Get checklist-specific fields
    if sampleset and sampleset.checklists:
        for checklist_name in sampleset.checklists:
            if checklist_name in Sampleset.checklist_structure:
                checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
                try:
                    ChecklistModel = apps.get_model('app', checklist_class_name)
                    checklist_instance = ChecklistModel.objects.filter(
                        sample=sample,
                        sampleset=sampleset
                    ).first()
                    
                    if checklist_instance:
                        fields_data['checklist_fields'][checklist_name] = {}
                        # Get all fields from the checklist model
                        for field in checklist_instance._meta.fields:
                            if field.name not in ['id', 'sample', 'sampleset', 'sample_type']:
                                value = getattr(checklist_instance, field.name)
                                if value:
                                    field_label = field.verbose_name if hasattr(field, 'verbose_name') else field.name.replace('_', ' ').title()
                                    fields_data['checklist_fields'][checklist_name][field_label] = str(value)
                except:
                    pass
    
    return JsonResponse(fields_data)


@staff_member_required
def admin_project_list(request):
    """
    List all projects with statistics for admin view
    """
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Base queryset with annotations for statistics
    projects = Project.objects.all().annotate(
        order_count=Count('order'),
        sample_count=Count('order__sample', filter=Q(order__sample__sample_type=SAMPLE_TYPE_NORMAL)),
    ).select_related('user')
    
    # Apply filters
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) |
            Q(alias__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    if status_filter == 'registered':
        projects = projects.filter(submitted=True)
    elif status_filter == 'not_registered':
        projects = projects.filter(submitted=False)
    
    # Calculate additional statistics for each project
    project_stats = []
    for project in projects:
        # Get all samples for this project
        samples = Sample.objects.filter(
            order__project=project,
            sample_type=SAMPLE_TYPE_NORMAL
        )
        
        # Count samples with files
        samples_with_files = 0
        for sample in samples:
            reads = Read.objects.filter(sample=sample)
            if reads.exists() and any(read.file_1 or read.file_2 for read in reads):
                samples_with_files += 1
        
        # Calculate file completion percentage
        file_completion = 0
        if samples.count() > 0:
            file_completion = int((samples_with_files / samples.count()) * 100)
        
        # Get latest order status for the project
        latest_order = project.order_set.order_by('-status_updated_at').first()
        
        # Get XML submission info
        project_submissions = ProjectSubmission.objects.filter(projects=project)
        submission_count = project_submissions.count()
        has_successful_submission = project_submissions.filter(accession_status='SUCCESSFUL').exists()
        
        project_stats.append({
            'project': project,
            'order_count': project.order_count,
            'sample_count': project.sample_count,
            'samples_with_files': samples_with_files,
            'file_completion': file_completion,
            'latest_order_status': latest_order.get_status_display() if latest_order else 'No orders',
            'has_all_files': samples_with_files == samples.count() and samples.count() > 0,
            'submission_count': submission_count,
            'has_successful_submission': has_successful_submission
        })
    
    # Pagination
    paginator = Paginator(project_stats, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_projects': len(project_stats),
    }
    
    return render(request, 'admin_project_list.html', context)


@staff_member_required
def admin_project_detail(request, project_id):
    """
    Detailed view of a project with workflow and statistics
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Get all orders for this project
    orders = project.order_set.all().order_by('-date')
    
    # Calculate project statistics
    total_samples = Sample.objects.filter(
        order__project=project,
        sample_type=SAMPLE_TYPE_NORMAL
    ).count()
    
    # Count samples with files
    samples_with_files = 0
    samples = Sample.objects.filter(
        order__project=project,
        sample_type=SAMPLE_TYPE_NORMAL
    )
    
    sample_file_details = []
    for sample in samples:
        reads = Read.objects.filter(sample=sample)
        has_files = reads.exists() and any(read.file_1 or read.file_2 for read in reads)
        if has_files:
            samples_with_files += 1
        
        sample_file_details.append({
            'sample': sample,
            'has_files': has_files,
            'read_count': reads.count()
        })
    
    # Calculate file completion percentage
    file_completion = 0
    if total_samples > 0:
        file_completion = int((samples_with_files / total_samples) * 100)
    
    # Check for existing pipeline runs (for future use)
    # pipeline_runs = Pipelines.objects.filter(samples__order__project=project).distinct()
    
    # Workflow status (all disabled for now)
    workflow_status = {
        'project_created': True,
        'ena_registered': project.submitted,
        'files_complete': samples_with_files == total_samples and total_samples > 0,
        'mag_pipeline_run': False,  # Will be implemented later
        'submg_pipeline_run': False,  # Will be implemented later
        'assemblies_uploaded': False,  # Will be implemented later
    }
    
    # Order statistics by status
    order_status_counts = {}
    for status_code, status_label in Order.STATUS_CHOICES:
        count = orders.filter(status=status_code).count()
        if count > 0:
            order_status_counts[status_label] = count
    
    # Get ProjectSubmissions for this project
    project_submissions = ProjectSubmission.objects.filter(projects=project).order_by('-id')
    
    context = {
        'project': project,
        'orders': orders,
        'total_samples': total_samples,
        'samples_with_files': samples_with_files,
        'file_completion': file_completion,
        'workflow_status': workflow_status,
        'order_status_counts': order_status_counts,
        'sample_file_details': sample_file_details[:10],  # Show first 10 samples
        'has_more_samples': len(sample_file_details) > 10,
        'project_submissions': project_submissions,
    }
    
    return render(request, 'admin_project_detail.html', context)


def calculate_md5(file_path):
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


@staff_member_required
@require_http_methods(["POST"])
def admin_simulate_reads(request, order_id):
    """
    Simulate reads for all samples in an order
    Based on the create_test_reads admin action
    """
    order = get_object_or_404(Order, id=order_id)
    
    # Get all samples for this order
    samples = Sample.objects.filter(order=order, sample_type=SAMPLE_TYPE_NORMAL)
    
    if not samples.exists():
        messages.error(request, 'No samples found for this order')
        return redirect('admin_order_detail', order_id=order.id)
    
    # Create LOCAL_DIR if it doesn't exist
    local_dir = getattr(settings, 'LOCAL_DIR', os.path.join(settings.MEDIA_ROOT, 'simulated_reads'))
    os.makedirs(local_dir, exist_ok=True)
    
    template_number = 1
    created_reads = 0
    
    for sample in samples:
        # Skip if sample already has reads
        if Read.objects.filter(sample=sample).exists():
            continue
            
        # Use template files or create dummy files
        template_1_path = f"template_{template_number}_1.fastq.gz"
        template_2_path = f"template_{template_number}_2.fastq.gz"
        
        # Look for templates in parent directory of LOCAL_DIR
        template_1 = os.path.join(os.path.dirname(local_dir), template_1_path)
        template_2 = os.path.join(os.path.dirname(local_dir), template_2_path)
        
        # If templates don't exist, create dummy files
        if not os.path.exists(template_1):
            template_1 = os.path.join(local_dir, 'dummy_template_1.fastq.gz')
            if not os.path.exists(template_1):
                # Create a dummy gzipped file
                import gzip
                with gzip.open(template_1, 'wb') as f:
                    f.write(b'@DUMMY\nACGT\n+\nIIII\n')
        
        if not os.path.exists(template_2):
            template_2 = os.path.join(local_dir, 'dummy_template_2.fastq.gz')
            if not os.path.exists(template_2):
                import gzip
                with gzip.open(template_2, 'wb') as f:
                    f.write(b'@DUMMY\nTGCA\n+\nIIII\n')
        
        # Create simulated read files
        sample_alias = sample.sample_alias or f"sample_{sample.id}"
        paired_read_1 = os.path.join(local_dir, f"{sample_alias}_1.fastq.gz")
        paired_read_2 = os.path.join(local_dir, f"{sample_alias}_2.fastq.gz")
        
        # Copy or create files
        try:
            if os.path.exists(template_1) and os.path.exists(template_2):
                shutil.copyfile(template_1, paired_read_1)
                shutil.copyfile(template_2, paired_read_2)
            else:
                # Create dummy files directly
                import gzip
                with gzip.open(paired_read_1, 'wb') as f:
                    f.write(f'@{sample_alias}_read1\nACGTACGTACGT\n+\nIIIIIIIIIIII\n'.encode())
                with gzip.open(paired_read_2, 'wb') as f:
                    f.write(f'@{sample_alias}_read2\nTGCATGCATGCA\n+\nIIIIIIIIIIII\n'.encode())
            
            # Calculate checksums
            paired_read_1_hash = calculate_md5(paired_read_1)
            paired_read_2_hash = calculate_md5(paired_read_2)
            
            # Create Read object
            if os.path.isfile(paired_read_1) and os.path.isfile(paired_read_2):
                read = Read.objects.create(
                    sample=sample, 
                    file_1=paired_read_1, 
                    file_2=paired_read_2, 
                    read_file_checksum_1=paired_read_1_hash, 
                    read_file_checksum_2=paired_read_2_hash
                )
                created_reads += 1
                
        except Exception as e:
            messages.error(request, f'Error creating reads for sample {sample_alias}: {str(e)}')
            continue
        
        template_number += 1
    
    if created_reads > 0:
        messages.success(request, f'Successfully simulated reads for {created_reads} samples')
        
        # Add a note about the simulation
        StatusNote.objects.create(
            order=order,
            user=request.user,
            note_type='internal',
            content=f'Simulated FASTQ reads for {created_reads} samples'
        )
    else:
        messages.info(request, 'All samples already have associated reads')
    
    return redirect('admin_order_detail', order_id=order.id)


@staff_member_required
@require_http_methods(["POST"])
def admin_generate_project_xml(request, project_id):
    """
    Generate ENA XML for a project and create ProjectSubmission
    """
    project = get_object_or_404(Project, id=project_id)
    
    try:
        # Create ProjectSubmission object
        project_submission = ProjectSubmission.objects.create()
        project_submission.projects.add(project)
        
        # Generate project XML using template
        context = {
            'projects': [project]
        }
        project_xml_content = render_to_string('admin/app/sample/project_xml_template.xml', context)
        project_submission.project_object_xml = project_xml_content
        
        # Load submission template
        submission_template_path = os.path.join(settings.BASE_DIR, 'app', 'templates', 'admin', 'app', 'sample', 'submission_template.xml')
        if os.path.exists(submission_template_path):
            with open(submission_template_path, 'r') as file:
                submission_xml_content = file.read()
            project_submission.submission_object_xml = submission_xml_content
        else:
            # Use a default submission template if file doesn't exist
            submission_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<SUBMISSION>
   <ACTIONS>
      <ACTION>
         <ADD/>
      </ACTION>
   </ACTIONS>
</SUBMISSION>'''
            project_submission.submission_object_xml = submission_xml_content
        
        project_submission.save()
        
        messages.success(request, f'Successfully created ProjectSubmission {project_submission.id} for project "{project.title}"')
        
        # Redirect based on where the request came from
        if 'HTTP_REFERER' in request.META and 'project-detail' in request.META['HTTP_REFERER']:
            return redirect('admin_project_detail', project_id=project.id)
        else:
            return redirect('admin_project_list')
            
    except Exception as e:
        messages.error(request, f'Error generating XML: {str(e)}')
        if 'HTTP_REFERER' in request.META:
            return redirect(request.META['HTTP_REFERER'])
        else:
            return redirect('admin_project_list')


@staff_member_required
def admin_submission_list(request):
    """
    List all project submissions with filtering and search
    """
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    
    # Base queryset
    submissions = ProjectSubmission.objects.all().prefetch_related('projects', 'projects__user').order_by('-id')
    
    # Apply filters
    if search_query:
        submissions = submissions.filter(
            Q(projects__title__icontains=search_query) |
            Q(projects__user__username__icontains=search_query) |
            Q(projects__user__email__icontains=search_query) |
            Q(projects__study_accession_id__icontains=search_query)
        ).distinct()
    
    if status_filter:
        if status_filter == 'pending':
            submissions = submissions.filter(
                project_object_xml__isnull=False,
                receipt_xml__isnull=True,
                accession_status__isnull=True
            )
        elif status_filter == 'submitted':
            submissions = submissions.filter(
                receipt_xml__isnull=False,
                accession_status__isnull=True
            )
        elif status_filter == 'successful':
            submissions = submissions.filter(accession_status='SUCCESSFUL')
        elif status_filter == 'failed':
            submissions = submissions.filter(
                receipt_xml__isnull=False
            ).exclude(accession_status='SUCCESSFUL')
    
    # Note: created_at field doesn't exist on ProjectSubmission model
    # if date_from:
    #     submissions = submissions.filter(created_at__gte=date_from)
    
    # Calculate statistics
    total_submissions = ProjectSubmission.objects.count()
    pending_count = ProjectSubmission.objects.filter(
        project_object_xml__isnull=False,
        receipt_xml__isnull=True,
        accession_status__isnull=True
    ).count()
    submitted_count = ProjectSubmission.objects.filter(
        receipt_xml__isnull=False,
        accession_status__isnull=True
    ).count()
    successful_count = ProjectSubmission.objects.filter(
        accession_status='SUCCESSFUL'
    ).count()
    
    # Pagination
    paginator = Paginator(submissions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_from': date_from,
        'total_submissions': total_submissions,
        'pending_count': pending_count,
        'submitted_count': submitted_count,
        'successful_count': successful_count,
    }
    
    return render(request, 'admin_submission_list.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_delete_submission(request, submission_id):
    """
    Delete a ProjectSubmission
    """
    submission = get_object_or_404(ProjectSubmission, id=submission_id)
    
    # Get project info for redirect
    project = submission.projects.first()
    
    # Delete the submission
    submission.delete()
    
    messages.success(request, f'Successfully deleted ProjectSubmission #{submission_id}')
    
    # Redirect based on where the request came from
    if 'HTTP_REFERER' in request.META:
        referer = request.META['HTTP_REFERER']
        if 'project-detail' in referer and project:
            return redirect('admin_project_detail', project_id=project.id)
        elif 'submissions' in referer:
            return redirect('admin_submission_list')
    
    # Default redirect
    return redirect('admin_submission_list')


@staff_member_required
@require_http_methods(["POST"])
def admin_register_project_ena(request, submission_id):
    """
    Register a ProjectSubmission with ENA
    Based on the register_projects admin action
    """
    import requests
    import xml.etree.ElementTree as ET
    from pathlib import Path
    
    submission = get_object_or_404(ProjectSubmission, id=submission_id)
    
    # Check if already submitted
    if submission.receipt_xml:
        messages.warning(request, 'This submission has already been registered with ENA.')
        return redirect(request.META.get('HTTP_REFERER', 'admin_project_list'))
    
    # Check for required environment variables
    if not all([settings.ENA_USERNAME, settings.ENA_PASSWORD]):
        messages.error(request, 'ENA credentials are not configured. Please set ENA_USERNAME and ENA_PASSWORD in your environment.')
        return redirect(request.META.get('HTTP_REFERER', 'admin_project_list'))
    
    try:
        # Create LOCAL_DIR if it doesn't exist
        local_dir = getattr(settings, 'LOCAL_DIR', os.path.join(settings.MEDIA_ROOT, 'ena_submissions'))
        Path(local_dir).mkdir(parents=True, exist_ok=True)
        
        # Save XML content to files
        project_xml_filename = os.path.join(local_dir, f"project_{submission.id}.xml")
        submission_xml_filename = os.path.join(local_dir, f"submission_{submission.id}.xml")
        
        with open(project_xml_filename, 'w') as project_file:
            project_file.write(submission.project_object_xml)
        with open(submission_xml_filename, 'w') as submission_file:
            submission_file.write(submission.submission_object_xml)
        
        # Prepare files for submission
        with open(submission_xml_filename, 'rb') as sub_file, open(project_xml_filename, 'rb') as proj_file:
            files = {
                'SUBMISSION': (os.path.basename(submission_xml_filename), sub_file),
                'PROJECT': (os.path.basename(project_xml_filename), proj_file),
            }
            
            # Prepare authentication
            auth = (settings.ENA_USERNAME, settings.ENA_PASSWORD)
            
            # Make the request to ENA test server
            response = requests.post(
                "https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/",
                files=files,
                auth=auth
            )
        
        # Clean up temporary files
        try:
            os.remove(project_xml_filename)
            os.remove(submission_xml_filename)
        except:
            pass
        
        if response.status_code == 200:
            # Parse the XML response
            root = ET.fromstring(response.content)
            receipt_xml = ET.tostring(root, encoding='unicode')
            submission.receipt_xml = receipt_xml
            
            if root.tag == 'RECEIPT':
                success = root.attrib.get('success', 'false')
                if success == 'true':
                    # Process successful submission
                    for child in root:
                        if child.tag == 'PROJECT':
                            alias = child.attrib.get('alias')
                            accession_number = child.attrib.get('accession')
                            
                            # Update all projects in this submission
                            for project in submission.projects.all():
                                if project.alias == alias:
                                    project.study_accession_id = accession_number
                                    project.submitted = True
                                    
                                    # Check for alternative accession
                                    for grandchild in child:
                                        if grandchild.tag == 'EXT_ID':
                                            alt_accession = grandchild.attrib.get('accession')
                                            if alt_accession:
                                                project.alternative_accession_id = alt_accession
                                    
                                    project.save()
                    
                    submission.accession_status = 'SUCCESSFUL'
                    submission.save()
                    
                    # Get the first accession number for the success message
                    first_accession = None
                    for project in submission.projects.all():
                        if project.study_accession_id:
                            first_accession = project.study_accession_id
                            break
                    
                    if first_accession:
                        messages.success(request, f'Successfully registered project with ENA! Accession: {first_accession}')
                    else:
                        messages.success(request, 'Successfully registered project with ENA!')
                else:
                    # Handle submission errors
                    error_msg = 'ENA submission failed. '
                    for child in root:
                        if child.tag == 'MESSAGES':
                            for msg in child:
                                if msg.tag == 'ERROR':
                                    error_msg += msg.text + ' '
                    
                    submission.accession_status = 'FAILED'
                    submission.save()
                    
                    messages.error(request, error_msg)
            else:
                messages.error(request, f'Unexpected response from ENA: {response.content[:200]}')
        else:
            messages.error(request, f'ENA submission failed with status code: {response.status_code}')
            
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Network error connecting to ENA: {str(e)}')
    except Exception as e:
        messages.error(request, f'Error registering with ENA: {str(e)}')
    
    # Redirect based on where the request came from
    if 'HTTP_REFERER' in request.META:
        referer = request.META['HTTP_REFERER']
        if 'project-detail' in referer:
            project = submission.projects.first()
            if project:
                return redirect('admin_project_detail', project_id=project.id)
        elif 'submissions' in referer:
            return redirect('admin_submission_list')
    
    return redirect('admin_project_list')