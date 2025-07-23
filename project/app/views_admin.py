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
import logging
from django.conf import settings

logger = logging.getLogger(__name__)
from django.template.loader import render_to_string
from pathlib import Path
import random

from .models import Order, Project, StatusNote, Sample, SAMPLE_TYPE_NORMAL, SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG, Sampleset, Read, ProjectSubmission, SiteSettings, SubMGRun, Assembly, Bin, Mag, Alignment, MagRun, MagRunInstance
from django.contrib.auth.models import User
from .forms import StatusUpdateForm, OrderNoteForm, OrderRejectionForm, UserEditForm, UserCreateForm, TechnicalDetailsForm, AdminSettingsForm


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
    
    # Get orders by status in simplified workflow
    orders_by_status = []
    
    # Count orders in each simplified status
    draft_count = Order.objects.filter(status='draft').count()
    submitted_count = Order.objects.filter(status='ready_for_sequencing').count()
    sequencing_count = Order.objects.filter(status__in=['sequencing_in_progress', 'sequencing_completed', 'data_processing']).count()
    
    # Count sequenced orders (all samples have reads)
    sequenced_count = 0
    completed_orders = Order.objects.filter(status__in=['data_delivered', 'completed'])
    for order in completed_orders:
        samples = order.sample_set.filter(sample_type=SAMPLE_TYPE_NORMAL)
        if samples.exists():
            has_all_reads = True
            for sample in samples:
                if not Read.objects.filter(sample=sample).exists():
                    has_all_reads = False
                    break
            if has_all_reads:
                sequenced_count += 1
    
    total_orders = stats['total_orders'] or 1  # Avoid division by zero
    
    # Simplified workflow with icons and colors
    orders_by_status = [
        {
            'code': 'draft',
            'label': 'Draft',
            'count': draft_count,
            'icon': 'fa-edit',
            'color': '#6c757d',  # grey
            'percentage': round((draft_count / total_orders) * 100, 1)
        },
        {
            'code': 'ready_for_sequencing',
            'label': 'Submitted',
            'count': submitted_count,
            'icon': 'fa-paper-plane',
            'color': '#3498db',  # blue
            'percentage': round((submitted_count / total_orders) * 100, 1)
        },
        {
            'code': 'sequencing',
            'label': 'Sequencing',
            'count': sequencing_count,
            'icon': 'fa-dna',
            'color': '#f39c12',  # orange
            'percentage': round((sequencing_count / total_orders) * 100, 1)
        },
        {
            'code': 'sequenced',
            'label': 'Sequenced',
            'count': sequenced_count,
            'icon': 'fa-check-circle',
            'color': '#27ae60',  # green
            'percentage': round((sequenced_count / total_orders) * 100, 1)
        },
    ]
    
    stats['orders_by_status'] = orders_by_status
    
    # Get recent orders (all statuses)
    recent_orders = Order.objects.select_related(
        'project', 'project__user'
    ).order_by('-status_updated_at')[:10]
    
    # Get recent activity (all types of notes/changes)
    recent_activity = StatusNote.objects.all().select_related(
        'order', 'order__project', 'user'
    ).order_by('-created_at')[:20]
    
    context = {
        'stats': stats,
        'recent_orders': recent_orders,
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
        if status_filter == 'sequencing':
            # Handle combined sequencing status
            orders = orders.filter(status__in=['sequencing_in_progress', 'sequencing_completed', 'data_processing'])
        elif status_filter == 'sequenced':
            # Handle sequenced orders (all samples have reads)
            orders = orders.filter(status__in=['data_delivered', 'completed'])
            # Further filter to only include orders where all samples have reads
            filtered_orders = []
            for order in orders:
                samples = order.sample_set.filter(sample_type=SAMPLE_TYPE_NORMAL)
                if samples.exists():
                    has_all_reads = True
                    for sample in samples:
                        if not Read.objects.filter(sample=sample).exists():
                            has_all_reads = False
                            break
                    if has_all_reads:
                        filtered_orders.append(order.id)
            orders = orders.filter(id__in=filtered_orders)
        else:
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
    
    # Calculate read statistics - only count reads with actual file paths
    samples_with_reads = 0
    samples_without_reads = 0
    for sample in samples:
        read = sample.read_set.first()
        if read and (read.file_1 or read.file_2):
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
        order_count=Count('order', distinct=True),
        sample_count=Count('order__sample', filter=Q(order__sample__sample_type=SAMPLE_TYPE_NORMAL), distinct=True),
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
        
        # Calculate workflow status
        has_mag_runs = MagRun.objects.filter(
            reads__sample__order__project=project
        ).distinct().exists()
        
        has_submg_runs = SubMGRun.objects.filter(
            order__project=project
        ).exists()
        
        workflow_status = {
            'project_created': True,
            'ena_registered': has_successful_submission,
            'files_complete': samples_with_files == samples.count() and samples.count() > 0,
            'mag_pipeline_run': has_mag_runs,
            'submg_pipeline_run': has_submg_runs,
        }
        
        # Count completed workflow steps
        workflow_progress = sum([
            workflow_status['project_created'],
            workflow_status['ena_registered'],
            workflow_status['files_complete'],
            workflow_status['mag_pipeline_run'],
            workflow_status['submg_pipeline_run'],
        ])
        
        project_stats.append({
            'project': project,
            'order_count': project.order_count,
            'sample_count': project.sample_count,
            'samples_with_files': samples_with_files,
            'file_completion': file_completion,
            'latest_order_status': latest_order.get_status_display() if latest_order else 'No orders',
            'has_all_files': samples_with_files == samples.count() and samples.count() > 0,
            'submission_count': submission_count,
            'has_successful_submission': has_successful_submission,
            'workflow_status': workflow_status,
            'workflow_progress': workflow_progress,
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
    
    # Check for successful ENA registration
    has_successful_ena_submission = ProjectSubmission.objects.filter(
        projects=project,
        accession_status='SUCCESSFUL'
    ).exists()
    
    # Workflow status (all disabled for now)
    workflow_status = {
        'project_created': True,
        'ena_registered': has_successful_ena_submission,
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
    
    # Get SubMG runs for all orders in this project
    submg_runs = SubMGRun.objects.filter(order__project=project).select_related('order').order_by('-id')
    
    # Update workflow status to reflect SubMG runs
    if submg_runs.exists():
        workflow_status['submg_pipeline_run'] = True
    
    # Get MAG runs for this project (through reads)
    mag_runs = MagRun.objects.filter(
        reads__sample__order__project=project
    ).distinct().order_by('-id')
    
    # Update workflow status to reflect MAG runs
    if mag_runs.exists():
        workflow_status['mag_pipeline_run'] = True
    
    # Get MAG pipeline outputs (Assemblies, Bins, Alignments)
    assemblies = Assembly.objects.filter(order__project=project).select_related('order').order_by('-id')
    bins = Bin.objects.filter(order__project=project).select_related('order').order_by('-id')
    alignments = Alignment.objects.filter(order__project=project).select_related('order', 'assembly').order_by('-id')
    
    # Update workflow status to reflect assemblies
    if assemblies.exists():
        workflow_status['assemblies_uploaded'] = True
    
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
        'submg_runs': submg_runs,
        'mag_runs': mag_runs,
        'assemblies': assemblies,
        'bins': bins,
        'alignments': alignments,
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
    created_files = 0
    files_created = []
    
    for sample in samples:
        # Use sample_id (like SAMPLE_1753087065861) for file names
        sample_identifier = sample.sample_id if hasattr(sample, 'sample_id') and sample.sample_id else sample.sample_alias
        
        # Skip if sample has no identifier
        if not sample_identifier:
            messages.warning(request, f'Sample ID {sample.id} has no sample_id or alias - skipping')
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
        
        # Create simulated read files using sample_id
        paired_read_1 = os.path.join(local_dir, f"{sample_identifier}_1.fastq.gz")
        paired_read_2 = os.path.join(local_dir, f"{sample_identifier}_2.fastq.gz")
        
        # Skip if files already exist
        if os.path.exists(paired_read_1) and os.path.exists(paired_read_2):
            continue
        
        # Copy or create files
        try:
            if os.path.exists(template_1) and os.path.exists(template_2):
                shutil.copyfile(template_1, paired_read_1)
                shutil.copyfile(template_2, paired_read_2)
            else:
                # Create dummy files directly
                import gzip
                with gzip.open(paired_read_1, 'wb') as f:
                    f.write(f'@{sample_identifier}_read1\nACGTACGTACGT\n+\nIIIIIIIIIIII\n'.encode())
                with gzip.open(paired_read_2, 'wb') as f:
                    f.write(f'@{sample_identifier}_read2\nTGCATGCATGCA\n+\nIIIIIIIIIIII\n'.encode())
            
            # Track created files
            if os.path.isfile(paired_read_1) and os.path.isfile(paired_read_2):
                created_files += 2
                files_created.append(f"{sample_identifier}_1.fastq.gz")
                files_created.append(f"{sample_identifier}_2.fastq.gz")
                
        except Exception as e:
            messages.error(request, f'Error creating files for sample {sample_identifier}: {str(e)}')
            continue
        
        template_number += 1
    
    # Report results
    if created_files > 0:
        # List first few files created
        sample_count = created_files // 2  # Two files per sample
        if len(files_created) <= 6:
            file_list = ', '.join(files_created)
            messages.success(request, f'Created {created_files} FASTQ files: {file_list}')
        else:
            file_list = ', '.join(files_created[:6])
            messages.success(request, f'Created {created_files} FASTQ files for {sample_count} samples: {file_list}...')
        
        # Add a detailed note
        StatusNote.objects.create(
            order=order,
            user=request.user,
            note_type='internal',
            content=f'Simulated {created_files} FASTQ files in {local_dir}. Files are ready to be linked using "Check for Read Files".'
        )
        
        messages.info(request, 'Files created in filesystem. Click "Check for Read Files" to link them to samples.')
    else:
        messages.info(request, f'All FASTQ files already exist in {local_dir}. No new files created.')
    
    return redirect('admin_order_detail', order_id=order.id)


@staff_member_required
@require_http_methods(["POST"])
def admin_check_read_files(request, order_id):
    """
    Check for existing FASTQ files in the configured sequencing data path
    and link them to samples if found.
    """
    from .models import SiteSettings, StatusNote, Read
    from .utils import discover_sequencing_files, calculate_md5
    
    order = get_object_or_404(Order, id=order_id)
    
    # Get the sequencing data path from settings
    site_settings = SiteSettings.get_settings()
    data_path = site_settings.sequencing_data_path
    
    if not data_path:
        # Use the simulated reads path as default
        data_path = getattr(settings, 'LOCAL_DIR', os.path.join(settings.MEDIA_ROOT, 'simulated_reads'))
        messages.info(request, f'Sequencing data path not configured. Using default path: {data_path}')
    
    # Discover files
    results = discover_sequencing_files(order, data_path)
    
    # Check for general errors
    if 'error' in results:
        messages.error(request, results['error'])
        return redirect('admin_order_detail', order_id=order.id)
    
    # Process the results
    created_reads = 0
    updated_reads = 0
    cleared_reads = 0
    errors = []
    samples_checked = 0
    
    for sample_id, result in results.items():
        samples_checked += 1
        sample = result['sample']
        
        # Check if sample already has a Read object
        existing_read = Read.objects.filter(sample=sample).first()
        
        # Report any errors for this sample
        if result['errors'] and not existing_read:
            sample_identifier = sample.sample_id if hasattr(sample, 'sample_id') and sample.sample_id else sample.sample_alias
            for error in result['errors']:
                errors.append(f"{sample_identifier}: {error}")
            continue
        
        # Handle cases based on what we found
        if result['file_1'] or result['file_2']:
            # Files were found
            try:
                # Calculate checksums
                checksum_1 = calculate_md5(result['file_1']) if result['file_1'] else None
                checksum_2 = calculate_md5(result['file_2']) if result['file_2'] else None
                
                if existing_read:
                    # Update existing Read object
                    existing_read.file_1 = result['file_1'] or ''
                    existing_read.file_2 = result['file_2'] or ''
                    existing_read.read_file_checksum_1 = checksum_1 or ''
                    existing_read.read_file_checksum_2 = checksum_2 or ''
                    existing_read.save()
                    updated_reads += 1
                else:
                    # Create new Read object
                    read = Read.objects.create(
                        sample=sample,
                        file_1=result['file_1'] or '',
                        file_2=result['file_2'] or '',
                        read_file_checksum_1=checksum_1 or '',
                        read_file_checksum_2=checksum_2 or ''
                    )
                    created_reads += 1
                
            except Exception as e:
                errors.append(f"{sample.sample_alias}: Error processing Read object - {str(e)}")
        else:
            # No files found
            if existing_read:
                # Check if the existing files still exist
                files_exist = False
                if existing_read.file_1 and os.path.exists(existing_read.file_1):
                    files_exist = True
                elif existing_read.file_2 and os.path.exists(existing_read.file_2):
                    files_exist = True
                
                if not files_exist:
                    # Clear the file paths since files don't exist
                    existing_read.file_1 = ''
                    existing_read.file_2 = ''
                    existing_read.read_file_checksum_1 = ''
                    existing_read.read_file_checksum_2 = ''
                    existing_read.save()
                    cleared_reads += 1
                    sample_identifier = sample.sample_id if hasattr(sample, 'sample_id') and sample.sample_id else sample.sample_alias
                    errors.append(f"{sample_identifier}: Previously linked files no longer exist - cleared file paths")
    
    # Report results
    if created_reads > 0 or updated_reads > 0 or cleared_reads > 0:
        # Build summary message
        actions = []
        if created_reads > 0:
            actions.append(f'linked {created_reads} new')
        if updated_reads > 0:
            actions.append(f'updated {updated_reads} existing')
        if cleared_reads > 0:
            actions.append(f'cleared {cleared_reads} missing')
        
        summary = f"Successfully {', '.join(actions)} read file(s)"
        messages.success(request, summary)
        
        # Add a status note
        note_content = f'Checked for FASTQ files in {data_path}: '
        note_parts = []
        if created_reads > 0:
            note_parts.append(f'{created_reads} new files linked')
        if updated_reads > 0:
            note_parts.append(f'{updated_reads} existing files updated')
        if cleared_reads > 0:
            note_parts.append(f'{cleared_reads} missing files cleared')
        
        StatusNote.objects.create(
            order=order,
            user=request.user,
            note_type='internal',
            content=note_content + ', '.join(note_parts)
        )
        
        # Check if all samples now have reads with valid files
        from .models import Sample, SAMPLE_TYPE_NORMAL
        total_samples = Sample.objects.filter(order=order, sample_type=SAMPLE_TYPE_NORMAL).count()
        
        # Count samples that have reads with actual file paths
        samples_with_valid_reads = 0
        for s in Sample.objects.filter(order=order, sample_type=SAMPLE_TYPE_NORMAL):
            read = Read.objects.filter(sample=s).first()
            if read and (read.file_1 or read.file_2):
                samples_with_valid_reads += 1
        
        if total_samples > 0 and samples_with_valid_reads == total_samples:
            # All samples have reads - automatically advance status
            if order.status == 'sequencing_in_progress' and order.can_advance_status():
                next_status = order.get_next_status()
                if next_status == 'sequencing_completed':
                    order.status = next_status
                    order.save()
                    
                    StatusNote.objects.create(
                        order=order,
                        user=request.user,
                        note_type='status_change',
                        content=f'Status automatically advanced to Sequencing Completed - all samples have read files'
                    )
                    
                    messages.info(request, 'Order status automatically advanced to Sequencing Completed')
    else:
        if samples_checked == 0:
            messages.info(request, 'All samples already have associated read files')
        else:
            messages.warning(request, f'No new read files found in {data_path}')
    
    # Report any errors
    if errors:
        for error in errors[:5]:  # Show first 5 errors
            messages.error(request, error)
        if len(errors) > 5:
            messages.error(request, f'... and {len(errors) - 5} more errors')
    
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
    
    # Check for required credentials
    from .utils import get_ena_credentials
    ena_username, ena_password, ena_test_mode, ena_center_name = get_ena_credentials()
    
    if not all([ena_username, ena_password]):
        messages.error(request, 'ENA credentials are not configured. Please set them in Site Settings.')
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
            auth = (ena_username, ena_password)
            
            # Make the request to ENA server
            submission_url = "https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/" if ena_test_mode else "https://www.ebi.ac.uk/ena/submit/drop-box/submit/"
            response = requests.post(
                submission_url,
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


@staff_member_required
def admin_settings(request):
    """
    Admin settings page for managing site-wide configuration including ENA credentials
    """
    # Get or create the singleton SiteSettings instance
    site_settings = SiteSettings.get_settings()
    
    if request.method == 'POST':
        form = AdminSettingsForm(request.POST)
        if form.is_valid():
            # Update site settings with form data
            cleaned_data = form.cleaned_data
            
            # Basic site information
            if cleaned_data.get('site_name'):
                site_settings.site_name = cleaned_data['site_name']
            if cleaned_data.get('organization_name'):
                site_settings.organization_name = cleaned_data['organization_name']
            if cleaned_data.get('organization_short_name'):
                site_settings.organization_short_name = cleaned_data['organization_short_name']
            if cleaned_data.get('tagline') is not None:
                site_settings.tagline = cleaned_data['tagline']
            
            # Sequencing Data Configuration
            if cleaned_data.get('sequencing_data_path') is not None:
                site_settings.sequencing_data_path = cleaned_data['sequencing_data_path']
            
            # ENA Configuration
            if cleaned_data.get('ena_username') is not None:
                site_settings.ena_username = cleaned_data['ena_username']
            
            # Handle password separately (only update if provided)
            if cleaned_data.get('ena_password'):
                site_settings.set_ena_password(cleaned_data['ena_password'])
            
            site_settings.ena_test_mode = cleaned_data.get('ena_test_mode', False)
            
            if cleaned_data.get('ena_center_name') is not None:
                site_settings.ena_center_name = cleaned_data['ena_center_name']
            
            # Contact Information
            if cleaned_data.get('contact_email') is not None:
                site_settings.contact_email = cleaned_data['contact_email']
            if cleaned_data.get('website_url') is not None:
                site_settings.website_url = cleaned_data['website_url']
            
            # Branding
            if cleaned_data.get('primary_color'):
                site_settings.primary_color = cleaned_data['primary_color']
            if cleaned_data.get('secondary_color'):
                site_settings.secondary_color = cleaned_data['secondary_color']
            
            # Save the settings
            site_settings.save()
            
            # Clear the cache to ensure new settings are loaded
            from django.core.cache import cache
            cache.delete('site_settings')
            
            messages.success(request, 'Settings have been updated successfully.')
            return redirect('admin_settings')
    else:
        # Populate form with current settings
        initial_data = {
            'site_name': site_settings.site_name,
            'organization_name': site_settings.organization_name,
            'organization_short_name': site_settings.organization_short_name,
            'tagline': site_settings.tagline,
            'sequencing_data_path': site_settings.sequencing_data_path,
            'ena_username': site_settings.ena_username,
            # Don't populate password field for security
            'ena_test_mode': site_settings.ena_test_mode,
            'ena_center_name': site_settings.ena_center_name,
            'contact_email': site_settings.contact_email,
            'website_url': site_settings.website_url,
            'primary_color': site_settings.primary_color,
            'secondary_color': site_settings.secondary_color,
        }
        form = AdminSettingsForm(initial=initial_data)
    
    # Check if ENA is configured
    ena_configured = site_settings.ena_configured
    
    context = {
        'form': form,
        'site_settings': site_settings,
        'ena_configured': ena_configured,
    }
    
    return render(request, 'admin_settings.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_generate_submg_run(request, project_id):
    """
    Generate SubMG run for a project and all its orders
    Based on the Django admin action generate_submg_run_including_children
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Create dependency object, which is a dictionary of object lists
    projects = []
    orders = []
    samples = []
    assembly_samples = []
    bin_samples = []
    mag_samples = []
    reads = []
    assemblys = []
    bins = []
    alignments = []
    
    # Collect the project and all its dependencies
    if not project.submitted and project not in projects:
        projects.append(project)
        for order in project.order_set.all():
            if order not in orders:
                orders.append(order)
                for sample in order.sample_set.all():
                    if sample.sample_type == SAMPLE_TYPE_NORMAL and sample not in samples:
                        samples.append(sample)
                        for read in sample.read_set.all():
                            if read not in reads:
                                reads.append(read)
                    elif sample.sample_type == SAMPLE_TYPE_ASSEMBLY and sample not in assembly_samples:
                        assembly_samples.append(sample)
                    elif sample.sample_type == SAMPLE_TYPE_BIN and sample not in bin_samples:
                        bin_samples.append(sample)
                    elif sample.sample_type == SAMPLE_TYPE_MAG and sample not in mag_samples:
                        mag_samples.append(sample)
                        
                for assembly in order.assembly_set.all():
                    if assembly not in assemblys:
                        assemblys.append(assembly)
                        for read in assembly.read.all():
                            if read not in reads:
                                reads.append(read)
                                
                for bin in order.bin_set.all():
                    if bin not in bins:
                        bins.append(bin)
                        
                for alignment in order.alignment_set.all():
                    if alignment not in alignments:
                        alignments.append(alignment)
    
    # Generate YAML content
    yaml = []
    for project in projects:
        yaml.extend(project.getSubMGYAML())
    
    # Get platform list from orders
    sequencingPlatforms = []
    for order in orders:
        sequencingPlatforms = order.getSubMGSequencingPlatforms(sequencingPlatforms)
        
    for order in orders:
        yaml.extend(order.getSubMGYAML(sequencingPlatforms))
        
        # Create SubMG run for this order
        if samples:
            yaml.extend(Sample.getSubMGYAMLHeader())
        for sample in samples:
            yaml.extend(sample.getSubMGYAML(SAMPLE_TYPE_NORMAL))
            
        if reads:
            yaml.extend(Read.getSubMGYAMLHeader())
        for read in reads:
            yaml.extend(read.getSubMGYAML())
            
        if assemblys:
            yaml.extend(Assembly.getSubMGYAMLHeader())
        for assembly in assemblys:
            yaml.extend(assembly.getSubMGYAML())
        for assembly_sample in assembly_samples:
            yaml.extend(assembly_sample.getSubMGYAML(SAMPLE_TYPE_ASSEMBLY))
        if assemblys:
            yaml.extend(Assembly.getSubMGYAMLFooter())
            
        if bins:
            yaml.extend(Bin.getSubMGYAMLHeader())
        for bin in bins:
            yaml.extend(bin.getSubMGYAML())
            break
            
        tax_ids = {}
        tax_ids_content = ""
        for bin_sample in bin_samples:
            bin = bin_sample.bin
            tax_ids[bin.file.split('/')[-1].replace(".fa.gz", "")] = [bin_sample.scientific_name, bin_sample.tax_id]
            
        for bin in bins:
            yaml.extend(bin.getSubMGYAMLTaxIDYAML())
            tax_ids_content = bin.getSubMGYAMLTaxIDContent(tax_ids)
            break
            
        for bin_sample in bin_samples:
            yaml.extend(bin_sample.getSubMGYAML(SAMPLE_TYPE_BIN))
            break
            
        if bins:
            yaml.extend(Bin.getSubMGYAMLFooter())
            
        if mag_samples:
            yaml.extend(Mag.getSubMGYAMLHeader())
            
        mag_data = {}
        for mag_sample in mag_samples:
            bin = mag_sample.bin
            mag_data[bin.bin_number] = mag_sample.mag_data
            
        for mag_sample in mag_samples:
            yaml.extend(Mag.getSubMGYAMLMagDataYAML(mag_sample.mag_data))
            break
            
        for mag_sample in mag_samples:
            yaml.extend(mag_sample.getSubMGYAML(SAMPLE_TYPE_MAG))
            break
            
        if alignments:
            yaml.extend(Alignment.getSubMGYAMLHeader())
        for alignment in alignments:
            yaml.extend(alignment.getSubMGYAML())
            break
            
        # Create SubMGRun object
        subMG_run = SubMGRun.objects.create(order=order)
        output = '\n'.join(yaml)
        if bins:
            subMG_run.tax_ids = tax_ids_content
        subMG_run.yaml = output
        
        # Save to temporary file
        output_file_path = "/tmp/output.txt"
        with open(output_file_path, 'w') as output_file:
            print(output, file=output_file)
            
        subMG_run.save()
        
        # Add many-to-many relationships
        subMG_run.projects.set(projects)
        subMG_run.samples.set(samples)
        subMG_run.reads.set(reads)
        subMG_run.assemblys.set(assemblys)
        subMG_run.bins.set(bins)
        
    messages.success(request, f"SubMG run generated successfully for project '{project.title}'.")
    
    # Redirect back to project detail page
    return redirect('admin_project_detail', project_id=project_id)


@staff_member_required
@require_http_methods(["POST"])
def admin_create_mag_run(request, project_id):
    """
    Create MAG run for a project based on all its reads
    Based on the Django admin action create_mag_run
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Get all reads from all orders and samples in this project
    reads = Read.objects.filter(
        sample__order__project=project
    ).distinct()
    
    if not reads.exists():
        messages.warning(request, f"No reads found for project '{project.title}'. Cannot create MAG run.")
        return redirect('admin_project_detail', project_id=project_id)
    
    # Create MAG run
    mag_run = MagRun.objects.create()
    mag_run.reads.set(reads)
    
    # Generate samplesheet content
    context = {
        'reads': reads,
    }
    samplesheet_content = render_to_string('admin/app/sample/mag_samplesheet.csv', context)
    mag_run.samplesheet_content = samplesheet_content
    
    # Generate cluster config
    context = {
        'settings': settings,
    }
    cluster_config = render_to_string('admin/app/sample/mag_cluster_config.cfg', context)
    mag_run.cluster_config = cluster_config
    
    mag_run.save()
    
    messages.success(request, f"MAG run created successfully for project '{project.title}' with {reads.count()} reads.")
    
    # Redirect back to project detail page
    return redirect('admin_project_detail', project_id=project_id)


@staff_member_required
@require_http_methods(["POST"])
def admin_start_mag_run(request, mag_run_id):
    """
    Start/execute a MAG pipeline run
    Based on the Django admin action start_run in MagRunAdmin
    """
    import random
    from . import async_calls
    
    mag_run = get_object_or_404(MagRun, id=mag_run_id)
    
    # Check if the MAG run already has reads
    if not mag_run.reads.exists():
        messages.error(request, "Cannot start MAG run: No reads associated with this run.")
        return redirect('admin_project_detail', project_id=mag_run.reads.first().sample.order.project.id)
    
    # Check if it's already running
    if mag_run.status == 'running':
        messages.warning(request, "MAG run is already running.")
        return redirect('admin_project_detail', project_id=mag_run.reads.first().sample.order.project.id)
    
    try:
        # Create a new temporary folder for the run
        run_id = random.randint(1000000, 9999999)
        run_folder = f"/tmp/mag_{run_id}"
        os.makedirs(run_folder, exist_ok=True)
        
        # Write samplesheet and cluster config to files
        with open(os.path.join(run_folder, 'samplesheet.csv'), 'w') as file:
            file.write(mag_run.samplesheet_content)
        
        with open(os.path.join(run_folder, 'cluster_config.cfg'), 'w') as file:
            file.write(mag_run.cluster_config)
        
        # Start the async job
        async_calls.run_mag(mag_run, run_folder)
        
        messages.success(request, f"MAG pipeline started successfully for run #{mag_run.id}")
        
    except Exception as e:
        messages.error(request, f"Failed to start MAG pipeline: {str(e)}")
        logger.error(f"Failed to start MAG run {mag_run_id}: {str(e)}")
    
    # Get project ID for redirect
    first_read = mag_run.reads.first()
    if first_read and first_read.sample and first_read.sample.order:
        project_id = first_read.sample.order.project.id
        return redirect('admin_project_detail', project_id=project_id)
    
    # Fallback to admin dashboard if we can't find project
    return redirect('admin_dashboard')


@staff_member_required
@require_http_methods(["POST"])
def admin_start_submg_run(request, submg_run_id):
    """
    Start/execute a SubMG pipeline run
    Based on the Django admin action start_run in SubMGRunAdmin
    """
    import random
    from . import async_calls
    
    submg_run = get_object_or_404(SubMGRun, id=submg_run_id)
    
    # Check if it's already running
    if submg_run.status == 'running':
        messages.warning(request, "SubMG run is already running.")
        return redirect('admin_project_detail', project_id=submg_run.order.project.id)
    
    try:
        # Create a new temporary folder for the run
        run_id = random.randint(1000000, 9999999)
        run_folder = os.path.join(settings.LOCAL_DIR, f"{run_id}")
        os.makedirs(run_folder, exist_ok=True)
        
        # Write SubMG YAML file with updated tax_ids path
        with open(os.path.join(run_folder, 'submg.yaml'), 'w') as file:
            file.write(submg_run.yaml.replace('tax_ids.txt', f'{run_folder}/tax_ids.txt'))
        
        # Write tax_ids.txt file
        with open(os.path.join(run_folder, 'tax_ids.txt'), 'w') as file:
            file.write(submg_run.tax_ids)
        
        # Create SubMG run instance
        submg_run_instance = submg_run.submgruninstance_set.create(
            run_folder=run_folder
        )
        
        # Start the async job
        async_calls.run_submg(submg_run, run_folder)
        
        messages.success(request, f"SubMG pipeline started successfully for run #{submg_run.id}")
        
    except Exception as e:
        messages.error(request, f"Failed to start SubMG pipeline: {str(e)}")
        logger.error(f"Failed to start SubMG run {submg_run_id}: {str(e)}")
    
    # Redirect back to project detail page
    return redirect('admin_project_detail', project_id=submg_run.order.project.id)


