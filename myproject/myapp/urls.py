from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/create/', views.order_view, name='order_view'),
    path('orders/<int:order_id>/edit/', views.order_view, name='order_view'),
    path('orders/<int:order_id>/delete/', views.delete_order, name='delete_order'),
    path('orders/<int:order_id>/samples/', views.samples_view, name='samples_view'),
    path('orders/<int:order_id>/mixs/<str:mixs_standard>/', views.mixs_view, name='mixs_view'),
]