from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView, UserViewSet, CustomerViewSet, CustomerAddressViewSet,
    ItemMasterViewSet, InventoryItemViewSet, InstallationViewSet,
    ServiceFollowUpViewSet, MaintenanceRecordViewSet,
    dashboard_stats, search, api_info,
    # Mobile compatibility endpoints
    mobile_customer_search, mobile_customer_addresses, mobile_installation_create,
    mobile_service_form_create, mobile_customer_create, mobile_installation_service_forms,
    mobile_installation_spare_parts, mobile_installation_scan_qr, mobile_installation_create_with_qr
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'customer-addresses', CustomerAddressViewSet, basename='customeraddress')
router.register(r'items', ItemMasterViewSet, basename='itemmaster')
router.register(r'inventory-items', InventoryItemViewSet, basename='inventoryitem')
router.register(r'installations', InstallationViewSet, basename='installation')
router.register(r'services', ServiceFollowUpViewSet, basename='servicefollowup')
router.register(r'maintenances', MaintenanceRecordViewSet, basename='maintenancerecord')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Public endpoints
    path('info/', api_info, name='api_info'),
    
    # Special endpoints
    path('dashboard-stats/', dashboard_stats, name='dashboard_stats'),
    path('search/', search, name='search'),
    
    # Mobile compatibility endpoints (for existing web templates)
    path('customers/search/', mobile_customer_search, name='mobile_customer_search'),
    path('customers/<int:customer_id>/addresses/', mobile_customer_addresses, name='mobile_customer_addresses'),
    path('installation/create/', mobile_installation_create, name='mobile_installation_create'),
    path('installation/scan-qr/', mobile_installation_scan_qr, name='mobile_installation_scan_qr'),
    path('installation/create-with-qr/', mobile_installation_create_with_qr, name='mobile_installation_create_with_qr'),
    path('service-form/create/', mobile_service_form_create, name='mobile_service_form_create'),
    path('customers/create/', mobile_customer_create, name='mobile_customer_create'),
    path('installation/<int:installation_id>/service-forms/', mobile_installation_service_forms, name='mobile_installation_service_forms'),
    path('installation/<int:installation_id>/spare-parts/', mobile_installation_spare_parts, name='mobile_installation_spare_parts'),
    
    # ViewSet URLs
    path('', include(router.urls)),
]
