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
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Use company-based permission system
        return get_company_queryset_for_user(self.request.user, Company.objects.all())
    
    @action(detail=True, methods=['get'])
    def addresses(self, request, pk=None):
        """Get customer addresses"""
        customer = self.get_object()
        addresses = customer.address.all()
        serializer = CustomerAddressSerializer(addresses, many=True)
        return Response(serializer.data)


class CustomerAddressViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CustomerAddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filter addresses based on companies user can access
        allowed_companies = get_company_queryset_for_user(self.request.user, Company.objects.all())
        return Address.objects.filter(company__in=allowed_companies)


# Item Master ViewSets
class ItemMasterViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ItemMasterSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filter items based on companies user can access
        allowed_companies = get_company_queryset_for_user(self.request.user, Company.objects.all())
        return ItemMaster.objects.filter(company__in=allowed_companies)


class InventoryItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filter inventory items based on companies user can access
        allowed_companies = get_company_queryset_for_user(self.request.user, Company.objects.all())
        return InventoryItem.objects.filter(
            name__company__in=allowed_companies
        ).select_related('name')


# Installation ViewSet
class InstallationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filter installations based on companies user can access
        allowed_companies = get_company_queryset_for_user(self.request.user, Company.objects.all())
        return Installation.objects.filter(
            customer__in=allowed_companies
        ).select_related('customer', 'inventory_item', 'user')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return InstallationCreateSerializer
        return InstallationSerializer


# Service ViewSet
class ServiceFollowUpViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filter services based on companies user can access
        allowed_companies = get_company_queryset_for_user(self.request.user, Company.objects.all())
        return ServiceFollowUp.objects.filter(
            installation__customer__in=allowed_companies
        ).select_related('installation')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ServiceFollowUpCreateSerializer
        return ServiceFollowUpSerializer


# Maintenance ViewSet
class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filter maintenance records based on companies user can access
        allowed_companies = get_company_queryset_for_user(self.request.user, Company.objects.all())
        return MaintenanceRecord.objects.filter(
            service_followup__installation__customer__in=allowed_companies
        ).select_related('service_followup__installation', 'technician')
    
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
        service_followup__installation__customer__in=companies,
        service_followup__next_service_date__lte=timezone.now().date()
    ).count()
    
    # Recent services (last 30 days)
    thirty_days_ago = timezone.now().date() - timezone.timedelta(days=30)
    recent_services = ServiceFollowUp.objects.filter(
        installation__customer__in=companies,
        created_at__gte=thirty_days_ago
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
        Q(email__icontains=query)
    )[:5]
    
    # Search items
    items = ItemMaster.objects.filter(company__in=companies).filter(
        Q(name__icontains=query) |
        Q(shortcode__icontains=query) |
        Q(brand_name__name__icontains=query)
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


# Mobile Template Compatibility Endpoints
@api_view(['GET'])
@permission_classes([AllowAny])  # Search doesn't need auth for now
def mobile_customer_search(request):
    """
    Customer search endpoint for mobile templates
    Compatible with: /warranty-services/api/customers/search/
    """
    query = request.GET.get('q', '')
    if not query:
        return Response({'results': []})
    
    # Use existing search functionality
    companies = Company.objects.filter(
        Q(name__icontains=query) |
        Q(email__icontains=query)
    )[:10]
    
    results = []
    for company in companies:
        results.append({
            'id': company.id,
            'name': company.name,
            'email': company.email,
            'telephone': company.telephone,
            'tax_number': company.tax_number,
        })
    
    return Response({'results': results})


@api_view(['GET'])
@permission_classes([AllowAny])  # Address lookup doesn't need auth for now
def mobile_customer_addresses(request, customer_id):
    """
    Get customer addresses for mobile templates
    Compatible with: /warranty-services/api/customers/{id}/addresses/
    """
    try:
        customer = Company.objects.get(id=customer_id)
        addresses = customer.address.all()
        
        results = []
        for address in addresses:
            results.append({
                'id': address.id,
                'name': address.name,
                'address': address.address,
                'city': address.city.name if address.city else None,
                'county': address.county.name if address.county else None,
                'district': address.district.name if address.district else None,
                'zipcode': address.zipcode,
            })
        
        return Response({'addresses': results})
        
    except Company.DoesNotExist:
        return Response({'error': 'Customer not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Installation creation needs auth
def mobile_installation_create(request):
    """
    Create installation for mobile templates
    Compatible with: /warranty-services/api/installation/create/
    """
    from warranty_and_services.models import Installation
    from item_master.models import InventoryItem
    
    try:
        data = request.data
        
        # Get required objects
        inventory_item = InventoryItem.objects.get(id=data.get('inventory_item_id'))
        customer = Company.objects.get(id=data.get('customer_id'))
        
        # Create installation
        installation = Installation.objects.create(
            user=request.user,  # Use authenticated user
            inventory_item=inventory_item,
            customer=customer,
            location_latitude=data.get('location_latitude'),
            location_longitude=data.get('location_longitude'),
            location_address=data.get('location_address', ''),
            installation_notes=data.get('installation_notes', ''),
        )
        
        return Response({
            'success': True,
            'installation_id': installation.id,
            'message': 'Installation created successfully'
        })
        
    except (InventoryItem.DoesNotExist, Company.DoesNotExist) as e:
        return Response({'error': str(e)}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Service creation needs auth
def mobile_service_form_create(request):
    """
    Create service follow-up for mobile templates
    Compatible with: /warranty-services/api/service-form/create/
    """
    from warranty_and_services.models import Installation, ServiceFollowUp
    from django.utils import timezone
    
    try:
        data = request.data
        
        # Get installation
        installation = Installation.objects.get(id=data.get('installation_id'))
        
        # Calculate next service date if not provided
        next_service_date = data.get('next_service_date')
        if not next_service_date:
            service_value = float(data.get('service_value', 6))
            if data.get('service_type') == 'time_term':
                # Add months to setup date
                from datetime import timedelta
                next_service_date = installation.setup_date + timedelta(days=int(service_value * 30))
            else:
                # Default to 6 months from now
                next_service_date = timezone.now() + timedelta(days=180)
        
        # Create service follow-up
        service = ServiceFollowUp.objects.create(
            installation=installation,
            service_type=data.get('service_type', 'time_term'),
            service_value=data.get('service_value', 6),
            next_service_date=next_service_date,
            calculation_notes=data.get('calculation_notes', ''),
        )
        
        return Response({
            'success': True,
            'service_id': service.id,
            'message': 'Service follow-up created successfully'
        })
        
    except Installation.DoesNotExist:
        return Response({'error': 'Installation not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Customer creation needs auth
def mobile_customer_create(request):
    """
    Create customer for mobile templates
    Compatible with: /warranty-services/api/customers/create/
    """
    try:
        data = request.data
        
        # Create customer
        customer = Company.objects.create(
            name=data.get('name'),
            email=data.get('email', ''),
            telephone=data.get('telephone', ''),
            tax_number=data.get('tax_number', ''),
            company_type='enduser',
        )
        
        return Response({
            'success': True,
            'customer_id': customer.id,
            'message': 'Customer created successfully'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])  # Service forms lookup doesn't need auth for now
def mobile_installation_service_forms(request, installation_id):
    """
    Get service forms for installation
    Compatible with: /warranty-services/api/installation/{id}/service-forms/
    """
    try:
        installation = Installation.objects.get(id=installation_id)
        
        # Get service forms from item master
        service_forms = installation.inventory_item.name.service_forms.all()
        
        results = []
        for form in service_forms:
            results.append({
                'id': form.id,
                'name': form.name,
            })
        
        return Response({'service_forms': results})
        
    except Installation.DoesNotExist:
        return Response({'error': 'Installation not found'}, status=404)


@api_view(['GET'])
@permission_classes([AllowAny])  # Spare parts lookup doesn't need auth for now
def mobile_installation_spare_parts(request, installation_id):
    """
    Get spare parts for installation
    Compatible with: /warranty-services/api/installation/{id}/spare-parts/
    """
    try:
        installation = Installation.objects.get(id=installation_id)
        
        # Get spare parts from item master
        from item_master.models import ItemSparePart
        spare_parts = ItemSparePart.objects.filter(
            main_item=installation.inventory_item.name
        ).select_related('spare_part_item')
        
        results = []
        for relation in spare_parts:
            spare_part = relation.spare_part_item
            results.append({
                'id': spare_part.id,
                'name': spare_part.name,
                'shortcode': spare_part.shortcode,
                'brand_name': spare_part.brand_name.name if spare_part.brand_name else None,
            })
        
        return Response({'spare_parts': results})
        
    except Installation.DoesNotExist:
        return Response({'error': 'Installation not found'}, status=404)
