from django.urls import path
from . import views, views_admin

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('project/create/', views.project_view, name='project_create'),
    path('project/<int:project_id>/edit/', views.project_view, name='project_edit'),
    path('project/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('project/<int:project_id>/orders/', views.OrderListView.as_view(), name='order_list'),
    path('project/<int:project_id>/orders/create/', views.order_view, name='order_create'),
    path('project/<int:project_id>/orders/<int:order_id>/edit/', views.order_view, name='order_edit'),
    path('project/<int:project_id>/orders/<int:order_id>/delete/', views.delete_order, name='delete_order'),
    path('project/<int:project_id>/orders/<int:order_id>/metadata/', views.metadata_view, name='metadata_view'),
    path('project/<int:project_id>/orders/<int:order_id>/field-selection/', views.field_selection_view, name='field_selection_view'),
    path('project/<int:project_id>/orders/<int:order_id>/field-selection/<str:checklist>/', views.field_selection_view, name='field_selection_view_with_checklist'),
    path('project/<int:project_id>/orders/<int:order_id>/samples/<int:sample_type>/', views.samples_view, name='samples_view'),
    path('test_submg/', views.test_submg, name='test_submg'),
    path('test_mag/', views.test_mag, name='test_mag'),

    # API endpoints
    path('api/orders/<int:order_id>/advance-status/', views.advance_order_status, name='advance_order_status'),
    
    # Admin views
    path('admin-dashboard/', views_admin.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/projects/', views_admin.admin_project_list, name='admin_project_list'),
    path('admin-dashboard/projects/<int:project_id>/', views_admin.admin_project_detail, name='admin_project_detail'),
    path('admin-dashboard/projects/<int:project_id>/generate-xml/', views_admin.admin_generate_project_xml, name='admin_generate_project_xml'),
    path('admin-dashboard/projects/<int:project_id>/generate-submg/', views_admin.admin_generate_submg_run, name='admin_generate_submg_run'),
    path('admin-dashboard/projects/<int:project_id>/create-mag-run/', views_admin.admin_create_mag_run, name='admin_create_mag_run'),
    path('admin-dashboard/mag-runs/<int:mag_run_id>/start/', views_admin.admin_start_mag_run, name='admin_start_mag_run'),
    path('admin-dashboard/submg-runs/<int:submg_run_id>/start/', views_admin.admin_start_submg_run, name='admin_start_submg_run'),
    path('admin-dashboard/submissions/', views_admin.admin_submission_list, name='admin_submission_list'),
    path('admin-dashboard/submissions/<int:submission_id>/delete/', views_admin.admin_delete_submission, name='admin_delete_submission'),
    path('admin-dashboard/submissions/<int:submission_id>/register-ena/', views_admin.admin_register_project_ena, name='admin_register_project_ena'),
    path('admin-dashboard/orders/', views_admin.admin_order_list, name='admin_order_list'),
    path('admin-dashboard/orders/<int:order_id>/', views_admin.admin_order_detail, name='admin_order_detail'),
    path('admin-dashboard/orders/<int:order_id>/update-status/', views_admin.admin_update_order_status, name='admin_update_order_status'),
    path('admin-dashboard/orders/<int:order_id>/add-note/', views_admin.admin_add_order_note, name='admin_add_order_note'),
    path('admin-dashboard/orders/<int:order_id>/update-technical/', views_admin.admin_update_technical_details, name='admin_update_technical_details'),
    path('admin-dashboard/samples/<int:sample_id>/fields/', views_admin.admin_get_sample_fields, name='admin_get_sample_fields'),
    path('admin-dashboard/orders/<int:order_id>/reject/', views_admin.admin_reject_order, name='admin_reject_order'),
    path('admin-dashboard/orders/<int:order_id>/simulate-reads/', views_admin.admin_simulate_reads, name='admin_simulate_reads'),
    path('admin-dashboard/orders/<int:order_id>/check-read-files/', views_admin.admin_check_read_files, name='admin_check_read_files'),
    path('admin-dashboard/orders/export/', views_admin.admin_export_orders, name='admin_export_orders'),
    path('admin-dashboard/orders/bulk-update/', views_admin.admin_bulk_update_status, name='admin_bulk_update_status'),
    
    # User management
    path('admin-dashboard/users/', views_admin.admin_user_list, name='admin_user_list'),
    path('admin-dashboard/users/<int:user_id>/edit/', views_admin.admin_user_edit, name='admin_user_edit'),
    path('admin-dashboard/users/create/', views_admin.admin_user_create, name='admin_user_create'),
    
    # Settings management
    path('admin-dashboard/settings/', views_admin.admin_settings, name='admin_settings'),
]