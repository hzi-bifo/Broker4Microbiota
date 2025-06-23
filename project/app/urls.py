from django.urls import path
from . import views

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
    path('project/<int:project_id>/orders/<int:order_id>/samples/<int:sample_type>/', views.samples_view, name='samples_view'),
    path('test_submg/', views.test_submg, name='test_submg'),
]