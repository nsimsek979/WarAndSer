from django.urls import path
from . import views

app_name = 'warranty_and_services'

urlpatterns = [
    # Installation
    path('installations/', views.InstallationListView.as_view(), name='installation_list'),
    path('installation/<int:installation_id>/', views.installation_detail, name='installation_detail'),
    
    # Mobile Main
    path('mobile/', views.mobile_main, name='mobile_main'),
    
    # Mobile Installation
    path('installation/mobile/', views.mobile_installation_scanner, name='mobile_installation_scanner'),
    path('installation/mobile/form/', views.mobile_installation_form, name='mobile_installation_form'),
    
    # Mobile Maintenance
    path('maintenance/mobile/', views.mobile_maintenance_scanner, name='mobile_maintenance_scanner'),
    path('maintenance/mobile/form/', views.mobile_maintenance_form, name='mobile_maintenance_form'),
    
    # API Endpoints for Mobile
    path('api/items/search-by-barcode/', views.api_search_by_barcode, name='api_search_by_barcode'),
    path('api/items/search-by-serial/', views.api_search_by_serial, name='api_search_by_serial'),
    path('api/customers/search/', views.api_customer_search, name='api_customer_search'),
    path('api/customers/create/', views.api_customer_create, name='api_customer_create'),
    path('api/installation/create/', views.api_installation_create, name='api_installation_create'),
    
    # API Endpoints for Maintenance
    path('api/installations/search-by-qr/', views.api_installation_search_by_qr, name='api_installation_search_by_qr'),
    path('api/installations/search-by-serial/', views.api_installation_search_by_serial, name='api_installation_search_by_serial'),
    path('api/installation/<int:installation_id>/service-forms/', views.api_installation_service_forms, name='api_installation_service_forms'),
    path('api/installation/<int:installation_id>/spare-parts/', views.api_installation_spare_parts, name='api_installation_spare_parts'),
    path('api/maintenance/create/', views.api_maintenance_create, name='api_maintenance_create'),
    path('api/maintenance/search/', views.api_maintenance_search, name='api_maintenance_search'),
    path('api/maintenance/item-detail/', views.api_maintenance_item_detail, name='api_maintenance_item_detail'),
    path('api/maintenance/submit/', views.api_maintenance_submit, name='api_maintenance_submit'),
    
    # Warranty tracking
    path('warranty-tracking/', views.warranty_tracking_list, name='warranty_tracking_list'),
    path('warranty/<int:warranty_id>/', views.warranty_detail, name='warranty_detail'),
    
    # Service tracking
    path('service-tracking/', views.service_tracking_list, name='service_tracking_list'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
    path('item/<int:installation_id>/service-history/', views.item_service_history, name='item_service_history'),
    
    # Installation Map
    path('installations/map/', views.installation_map_view, name='installation_map'),
]
