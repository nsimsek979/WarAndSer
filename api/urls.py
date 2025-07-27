from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView, UserViewSet, CustomerViewSet, CustomerAddressViewSet,
    ItemMasterViewSet, InventoryItemViewSet, InstallationViewSet,
    ServiceFollowUpViewSet, MaintenanceRecordViewSet,
    dashboard_stats, search, api_info
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
    
    # ViewSet URLs
    path('', include(router.urls)),
]
