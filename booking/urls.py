from django.urls import path
from . import views

urlpatterns = [
    path('select-date/', views.select_date, name='select_date'),
    path('select-timeslot/', views.select_timeslot, name='select_timeslot'),
    path('select-game/', views.select_game, name='select_game'),
    path('summary/', views.booking_summary, name='booking_summary'),
    path('success/', views.booking_success, name='booking_success'),
    path('history/', views.booking_history, name='booking_history'),
    path('cancel/<int:pk>/', views.cancel_booking, name='cancel_booking'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/bookings/', views.admin_booking_list, name='admin_booking_list'),
    path('admin/bookings/add/', views.admin_booking_create, name='admin_booking_create'),
    path('admin/bookings/<int:pk>/edit/', views.admin_booking_update, name='admin_booking_update'),
    path('admin/bookings/<int:pk>/delete/', views.admin_booking_delete, name='admin_booking_delete'),
    path('admin/store/', views.admin_store_management, name='admin_store_management'),
    path('admin/store/add/', views.admin_game_create, name='admin_game_create'),
    path('admin/store/<int:pk>/edit/', views.admin_game_update, name='admin_game_update'),
    path('admin/store/<int:pk>/delete/', views.admin_game_delete, name='admin_game_delete'),
    path('admin/tables/', views.admin_table_list, name='admin_table_list'),
    path('admin/tables/add/', views.admin_table_create, name='admin_table_create'),
    path('admin/tables/<int:pk>/edit/', views.admin_table_update, name='admin_table_update'),
    path('admin/tables/<int:pk>/delete/', views.admin_table_delete, name='admin_table_delete'),
    path('admin/customers/', views.admin_customer_list, name='admin_customer_list'),
    path('admin/customers/<int:pk>/edit/', views.admin_customer_update, name='admin_customer_update'),
    path('admin/customers/<int:pk>/delete/', views.admin_customer_delete, name='admin_customer_delete'),
]
