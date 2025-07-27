from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.db.models import Q

from customer.models import Company, Address
from warranty_and_services.models import (
    Installation, ServiceFollowUp, MaintenanceRecord
)
from item_master.models import ItemMaster, InventoryItem
from custom_user.permissions import get_company_queryset_for_user

from .serializers import (
    UserSerializer, CustomerSerializer, CustomerAddressSerializer,
    ItemMasterSerializer, InventoryItemSerializer, InstallationSerializer, 
    InstallationCreateSerializer, ServiceFollowUpSerializer, ServiceFollowUpCreateSerializer,
    MaintenanceRecordSerializer, MaintenanceRecordCreateSerializer
)

User = get_user_model()


# Authentication Views
class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view that returns user data along with tokens"""
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Get user data
            user = User.objects.get(username=request.data.get('username'))
            user_serializer = UserSerializer(user)
            response.data['user'] = user_serializer.data
        return response


# User Profile ViewSet
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


# Customer ViewSets
class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [AllowAny]  # Test için geçici
    
    def get_queryset(self):
        # Test için basit queryset
        return Company.objects.all()
    
    @action(detail=True, methods=['get'])
    def addresses(self, request, pk=None):
        """Get customer addresses"""
        customer = self.get_object()
        addresses = customer.addresses.all()
        serializer = CustomerAddressSerializer(addresses, many=True)
        return Response(serializer.data)


class CustomerAddressViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CustomerAddressSerializer
    permission_classes = [AllowAny]  # Test için geçici
    
    def get_queryset(self):
        return Address.objects.all()


# Item Master ViewSets
class ItemMasterViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ItemMasterSerializer
    permission_classes = [AllowAny]  # Test için geçici
    
    def get_queryset(self):
        return ItemMaster.objects.all()


class InventoryItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InventoryItemSerializer
    permission_classes = [AllowAny]  # Test için geçici
    
    def get_queryset(self):
        return InventoryItem.objects.all().select_related('name')


# Installation ViewSet
class InstallationViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]  # Test için geçici
    
    def get_queryset(self):
        return Installation.objects.all().select_related('customer', 'inventory_item', 'user')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return InstallationCreateSerializer
        return InstallationSerializer


# Service ViewSet
class ServiceFollowUpViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]  # Test için geçici
    
    def get_queryset(self):
        return ServiceFollowUp.objects.all().select_related('installation')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ServiceFollowUpCreateSerializer
        return ServiceFollowUpSerializer


# Maintenance ViewSet
class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]  # Test için geçici
    
    def get_queryset(self):
        return MaintenanceRecord.objects.all().select_related('installation')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MaintenanceRecordCreateSerializer
        return MaintenanceRecordSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics for mobile app
    """
    companies = get_company_queryset_for_user(request.user, Company.objects.all())
    
    # Get counts
    total_installations = Installation.objects.filter(customer__in=companies).count()
    total_customers = companies.count()
    
    # Due maintenances (next maintenance date is overdue)
    from django.utils import timezone
    due_maintenances = MaintenanceRecord.objects.filter(
        installation__customer__in=companies,
        next_maintenance_date__lte=timezone.now().date()
    ).count()
    
    # Recent services (last 30 days)
    thirty_days_ago = timezone.now().date() - timezone.timedelta(days=30)
    recent_services = ServiceFollowUp.objects.filter(
        installation__customer__in=companies,
        service_date__gte=thirty_days_ago
    ).count()
    
    stats = {
        'total_installations': total_installations,
        'total_customers': total_customers,
        'due_maintenances': due_maintenances,
        'recent_services': recent_services,
    }
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search(request):
    """
    Search across installations, customers, and items
    """
    query = request.GET.get('q', '')
    if not query:
        return Response({'results': []})
    
    companies = get_company_queryset_for_user(request.user, Company.objects.all())
    
    # Search installations
    installations = Installation.objects.filter(
        customer__in=companies
    ).filter(
        Q(customer__name__icontains=query) |
        Q(installation_notes__icontains=query) |
        Q(location_address__icontains=query)
    ).select_related('customer')[:5]
    
    # Search customers
    customers = companies.filter(
        Q(name__icontains=query) |
        Q(contact_person__icontains=query) |
        Q(email__icontains=query)
    )[:5]
    
    # Search items
    items = ItemMaster.objects.filter(company__in=companies).filter(
        Q(item_name__icontains=query) |
        Q(item_number__icontains=query) |
        Q(brand__icontains=query) |
        Q(model__icontains=query)
    )[:5]
    
    results = {
        'installations': InstallationSerializer(installations, many=True).data,
        'customers': CustomerSerializer(customers, many=True).data,
        'items': ItemMasterSerializer(items, many=True).data,
    }
    
    return Response({'results': results})


@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """
    Public API info endpoint - no authentication required
    """
    info = {
        'api_name': 'Garanti ve Servis Mobile API',
        'version': '1.0',
        'description': 'REST API for mobile Android application',
        'endpoints': {
            'auth': {
                'login': '/api/auth/login/',
                'refresh': '/api/auth/refresh/',
            },
            'data': {
                'customers': '/api/customers/',
                'installations': '/api/installations/',
                'services': '/api/services/',
                'maintenances': '/api/maintenances/',
                'items': '/api/items/',
                'inventory': '/api/inventory-items/',
            },
            'utils': {
                'dashboard_stats': '/api/dashboard-stats/',
                'search': '/api/search/?q=term',
            }
        },
        'authentication': 'JWT Bearer Token',
        'note': 'All endpoints except /auth/* require authentication'
    }
    
    return Response(info)
