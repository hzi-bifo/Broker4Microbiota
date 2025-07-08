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
from django.views.decorators.http import require_http_methods
from collections import OrderedDict
import csv

from .models import Order, Project, StatusNote, Sample, User, SAMPLE_TYPE_NORMAL
from .forms import StatusUpdateForm, OrderNoteForm, OrderRejectionForm


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
    
    # Get recent activity (last 20 status changes)
    recent_activity = StatusNote.objects.filter(
        note_type='status_change'
    ).select_related('order', 'order__project', 'user').order_by('-created_at')[:20]
    
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
    
    # Get all samples for this order
    samples = Sample.objects.filter(order=order, sample_type=SAMPLE_TYPE_NORMAL)
    
    # Get status history and notes
    status_history = order.get_status_history()
    all_notes = order.get_notes(include_internal=True)
    
    # Initialize forms
    status_form = StatusUpdateForm(instance=order)
    note_form = OrderNoteForm()
    rejection_form = OrderRejectionForm()
    
    context = {
        'order': order,
        'project': order.project,
        'samples': samples,
        'status_history': status_history,
        'all_notes': all_notes,
        'status_form': status_form,
        'note_form': note_form,
        'rejection_form': rejection_form,
        'can_advance': order.can_advance_status(),
        'next_status': order.get_next_status(),
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