from rest_framework import serializers
from django.contrib.auth import get_user_model
from customer.models import Company, Address, ContactPerson, WorkingHours
from warranty_and_services.models import (
    Installation, ServiceFollowUp, MaintenanceRecord
)
from item_master.models import ItemMaster, InventoryItem

User = get_user_model()


# Authentication serializers
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'company']
        read_only_fields = ['id']


# Customer serializers
class ContactPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactPerson
        fields = ['id', 'full_name', 'title', 'email', 'telephone', 'created_at']


class WorkingHoursSerializer(serializers.ModelSerializer):
    weekly_working_hours = serializers.ReadOnlyField()
    working_days_per_week = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkingHours
        fields = [
            'id', 'daily_working_hours', 'working_on_saturday', 'working_on_sunday',
            'weekly_working_hours', 'working_days_per_week', 'created_at', 'updated_at'
        ]
    
    def get_working_days_per_week(self, obj):
        return obj.get_working_days_per_week()


class CustomerAddressSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    county_name = serializers.CharField(source='county.name', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    country_name = serializers.CharField(source='country.name', read_only=True)
    
    class Meta:
        model = Address
        fields = [
            'id', 'name', 'address', 'zipcode', 'city', 'county', 
            'district', 'country', 'city_name', 'county_name', 
            'district_name', 'country_name', 'created_at'
        ]


class CustomerSerializer(serializers.ModelSerializer):
    address = CustomerAddressSerializer(many=True, read_only=True)
    contact_persons = ContactPersonSerializer(source='contactperson_set', many=True, read_only=True)
    working_hours = WorkingHoursSerializer(read_only=True)
    installed_items = serializers.SerializerMethodField()
    service_tracking = serializers.SerializerMethodField()
    company_type_display = serializers.CharField(source='get_company_type_display', read_only=True)
    core_business_name = serializers.CharField(source='core_business.name', read_only=True)
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'email', 'telephone', 'tax_number', 
            'company_type', 'company_type_display', 'core_business_name',
            'active', 'created_at', 'address', 'contact_persons', 
            'working_hours', 'installed_items', 'service_tracking'
        ]
    
    def get_installed_items(self, obj):
        """Get all installed inventory items for this customer"""
        from warranty_and_services.models import Installation
        
        installations = Installation.objects.filter(customer=obj).select_related(
            'inventory_item', 'inventory_item__name', 'user'
        ).order_by('-setup_date')
        
        installed_items = []
        for installation in installations:
            item_data = {
                'installation_id': installation.id,
                'setup_date': installation.setup_date,
                'inventory_item': {
                    'id': installation.inventory_item.id,
                    'serial_no': installation.inventory_item.serial_no,
                    'item_master': {
                        'id': installation.inventory_item.name.id,
                        'name': installation.inventory_item.name.name,
                        'shortcode': installation.inventory_item.name.shortcode,
                        'brand_name': installation.inventory_item.name.brand_name.name if installation.inventory_item.name.brand_name else None,
                    }
                },
                'location_address': installation.location_address,
                'installation_notes': installation.installation_notes,
                'installer': {
                    'id': installation.user.id,
                    'name': f"{installation.user.first_name} {installation.user.last_name}".strip() or installation.user.username
                }
            }
            installed_items.append(item_data)
        
        return installed_items
    
    def get_service_tracking(self, obj):
        """Get service tracking information for this customer"""
        from warranty_and_services.models import Installation, ServiceFollowUp, MaintenanceRecord
        from django.utils import timezone
        
        # Get all installations for this customer
        installations = Installation.objects.filter(customer=obj)
        
        service_data = {
            'total_installations': installations.count(),
            'active_services': [],
            'completed_services': [],
            'overdue_services': [],
            'maintenance_records': []
        }
        
        # Get all service follow-ups for customer's installations
        service_followups = ServiceFollowUp.objects.filter(
            installation__customer=obj
        ).select_related(
            'installation', 'installation__inventory_item', 'installation__inventory_item__name'
        ).order_by('-next_service_date')
        
        now = timezone.now()
        
        for followup in service_followups:
            service_info = {
                'id': followup.id,
                'installation_id': followup.installation.id,
                'item_name': followup.installation.inventory_item.name.name,
                'item_serial': followup.installation.inventory_item.serial_no,
                'service_type': followup.service_type,
                'service_type_display': followup.get_service_type_display(),
                'service_value': followup.service_value,
                'next_service_date': followup.next_service_date,
                'is_completed': followup.is_completed,
                'completed_date': followup.completed_date,
                'location_address': followup.installation.location_address,
            }
            
            if followup.is_completed:
                service_data['completed_services'].append(service_info)
            elif followup.next_service_date <= now:
                service_data['overdue_services'].append(service_info)
            else:
                service_data['active_services'].append(service_info)
        
        # Get maintenance records
        maintenance_records = MaintenanceRecord.objects.filter(
            service_followup__installation__customer=obj
        ).select_related(
            'service_followup', 'service_followup__installation', 
            'service_followup__installation__inventory_item__name', 'technician'
        ).order_by('-maintenance_date')[:10]  # Son 10 bakım kaydı
        
        for record in maintenance_records:
            maintenance_info = {
                'id': record.id,
                'installation_id': record.service_followup.installation.id,
                'item_name': record.service_followup.installation.inventory_item.name.name,
                'item_serial': record.service_followup.installation.inventory_item.serial_no,
                'maintenance_type': record.maintenance_type,
                'maintenance_type_display': record.get_maintenance_type_display(),
                'service_date': record.service_date,
                'maintenance_date': record.maintenance_date,
                'technician_name': f"{record.technician.first_name} {record.technician.last_name}".strip() if record.technician else None,
                'breakdown_reason': record.breakdown_reason,
                'notes': record.notes,
            }
            service_data['maintenance_records'].append(maintenance_info)
        
        # Summary counts
        service_data['summary'] = {
            'total_active': len(service_data['active_services']),
            'total_overdue': len(service_data['overdue_services']),
            'total_completed': len(service_data['completed_services']),
            'total_maintenance_records': maintenance_records.count() if hasattr(maintenance_records, 'count') else len(service_data['maintenance_records'])
        }
        
        return service_data


# Item Master serializers
class WarrantyValueSerializer(serializers.ModelSerializer):
    warranty_type_name = serializers.CharField(source='warranty_type.type', read_only=True)
    
    class Meta:
        from item_master.models import WarrantyValue
        model = WarrantyValue
        fields = ['id', 'warranty_type', 'warranty_type_name', 'value', 'created_at']


class ServiceFormSerializer(serializers.ModelSerializer):
    class Meta:
        from item_master.models import ServiceForm
        model = ServiceForm
        fields = ['id', 'name', 'created_at']


class ItemMasterSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.category_name', read_only=True)
    brand_name_display = serializers.CharField(source='brand_name.name', read_only=True)
    stock_type_name = serializers.CharField(source='stock_type.name', read_only=True)
    status_name = serializers.CharField(source='status.status', read_only=True)
    spare_parts = serializers.SerializerMethodField()
    used_as_spare_part_for = serializers.SerializerMethodField()
    warranties = WarrantyValueSerializer(many=True, read_only=True)
    service_forms = ServiceFormSerializer(many=True, read_only=True)
    maintenance_schedules = serializers.SerializerMethodField()
    
    class Meta:
        model = ItemMaster
        fields = [
            'id', 'shortcode', 'name', 'description', 'category', 'category_name',
            'brand_name', 'brand_name_display', 'stock_type', 'stock_type_name',
            'status', 'status_name', 'slug', 'created_at', 'spare_parts', 
            'used_as_spare_part_for', 'warranties', 'service_forms', 'maintenance_schedules'
        ]
    
    def get_spare_parts(self, obj):
        """Get all spare parts for this item"""
        from item_master.models import ItemSparePart
        
        spare_part_relations = ItemSparePart.objects.filter(
            main_item=obj
        ).select_related('spare_part_item', 'spare_part_item__brand_name', 'spare_part_item__category')
        
        spare_parts = []
        for relation in spare_part_relations:
            spare_part = relation.spare_part_item
            spare_part_data = {
                'id': spare_part.id,
                'shortcode': spare_part.shortcode,
                'name': spare_part.name,
                'description': spare_part.description,
                'brand_name': spare_part.brand_name.name if spare_part.brand_name else None,
                'category_name': spare_part.category.category_name if spare_part.category else None,
                'stock_type_name': spare_part.stock_type.name if spare_part.stock_type else None,
                'status_name': spare_part.status.status if spare_part.status else None,
                'relation_created_at': relation.created_at
            }
            spare_parts.append(spare_part_data)
        
        return spare_parts
    
    def get_used_as_spare_part_for(self, obj):
        """Get all items that use this item as a spare part"""
        from item_master.models import ItemSparePart
        
        main_item_relations = ItemSparePart.objects.filter(
            spare_part_item=obj
        ).select_related('main_item', 'main_item__brand_name', 'main_item__category')
        
        main_items = []
        for relation in main_item_relations:
            main_item = relation.main_item
            main_item_data = {
                'id': main_item.id,
                'shortcode': main_item.shortcode,
                'name': main_item.name,
                'description': main_item.description,
                'brand_name': main_item.brand_name.name if main_item.brand_name else None,
                'category_name': main_item.category.category_name if main_item.category else None,
                'relation_created_at': relation.created_at
            }
            main_items.append(main_item_data)
        
        return main_items
    
    def get_maintenance_schedules(self, obj):
        """Get maintenance schedules for this item"""
        from item_master.models import MaintenanceSchedule
        
        schedules = MaintenanceSchedule.objects.filter(
            item_master=obj
        ).select_related(
            'service_period_value', 
            'service_period_value__service_period_type'
        ).order_by('service_period_value__value')
        
        maintenance_schedules = []
        for schedule in schedules:
            schedule_data = {
                'id': schedule.id,
                'service_period_type': schedule.service_period_value.service_period_type.type,
                'service_period_unit': schedule.service_period_value.service_period_type.unit,
                'service_period_value': schedule.service_period_value.value,
                'service_period_description': schedule.service_period_value.description,
                'is_critical': schedule.is_critical,
                'maintenance_description': schedule.maintenance_description,
                'created_at': schedule.created_at
            }
            maintenance_schedules.append(schedule_data)
        
        return maintenance_schedules


class InventoryItemSerializer(serializers.ModelSerializer):
    item_master = ItemMasterSerializer(source='name', read_only=True)
    item_name = serializers.CharField(source='name.name', read_only=True)
    item_shortcode = serializers.CharField(source='name.shortcode', read_only=True)
    warranty_tracking = serializers.SerializerMethodField()
    service_tracking = serializers.SerializerMethodField()
    installation_info = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'item_master', 'item_name', 'item_shortcode', 'serial_no', 
            'quantity', 'production_date', 'in_used', 'qr_code_image',
            'created_at', 'updated_at', 'warranty_tracking', 'service_tracking',
            'installation_info'
        ]
    
    def get_installation_info(self, obj):
        """Get installation information for this inventory item"""
        from warranty_and_services.models import Installation
        
        try:
            installation = Installation.objects.select_related(
                'customer', 'user'
            ).get(inventory_item=obj)
            
            return {
                'id': installation.id,
                'setup_date': installation.setup_date,
                'customer': {
                    'id': installation.customer.id,
                    'name': installation.customer.name,
                    'email': installation.customer.email
                },
                'location_address': installation.location_address,
                'installation_notes': installation.installation_notes,
                'installer': {
                    'id': installation.user.id,
                    'name': f"{installation.user.first_name} {installation.user.last_name}".strip() or installation.user.username
                }
            }
        except Installation.DoesNotExist:
            return None
    
    def get_warranty_tracking(self, obj):
        """Get warranty tracking information for this inventory item"""
        from warranty_and_services.models import Installation
        from django.utils import timezone
        from datetime import timedelta
        
        try:
            installation = Installation.objects.get(inventory_item=obj)
            setup_date = installation.setup_date
            now = timezone.now()
            
            # Get warranties from ItemMaster
            warranties = obj.name.warranties.select_related('warranty_type').all()
            
            warranty_info = {
                'installation_date': setup_date,
                'warranties': [],
                'warranty_status': 'not_installed'
            }
            
            if setup_date:
                warranty_info['warranty_status'] = 'active'
                
                for warranty in warranties:
                    # Calculate warranty end date based on type
                    if 'ay' in warranty.warranty_type.type.lower() or 'month' in warranty.warranty_type.type.lower():
                        # Monthly warranty (approximate: 30 days per month)
                        end_date = setup_date + timedelta(days=int(warranty.value * 30))
                    elif 'yıl' in warranty.warranty_type.type.lower() or 'year' in warranty.warranty_type.type.lower():
                        # Yearly warranty (approximate: 365 days per year)
                        end_date = setup_date + timedelta(days=int(warranty.value * 365))
                    elif 'gün' in warranty.warranty_type.type.lower() or 'day' in warranty.warranty_type.type.lower():
                        # Daily warranty
                        end_date = setup_date + timedelta(days=int(warranty.value))
                    else:
                        # Default to months (30 days each)
                        end_date = setup_date + timedelta(days=int(warranty.value * 30))
                    
                    is_expired = now > end_date
                    days_remaining = (end_date - now).days if not is_expired else 0
                    
                    warranty_data = {
                        'id': warranty.id,
                        'warranty_type': warranty.warranty_type.type,
                        'warranty_value': warranty.value,
                        'start_date': setup_date,
                        'end_date': end_date,
                        'is_expired': is_expired,
                        'days_remaining': days_remaining,
                        'status': 'expired' if is_expired else ('expiring_soon' if days_remaining <= 30 else 'active')
                    }
                    warranty_info['warranties'].append(warranty_data)
                
                # Overall warranty status
                active_warranties = [w for w in warranty_info['warranties'] if not w['is_expired']]
                if not active_warranties:
                    warranty_info['warranty_status'] = 'expired'
                elif any(w['days_remaining'] <= 30 for w in active_warranties):
                    warranty_info['warranty_status'] = 'expiring_soon'
            
            return warranty_info
            
        except Installation.DoesNotExist:
            return {
                'installation_date': None,
                'warranties': [],
                'warranty_status': 'not_installed'
            }
    
    def get_service_tracking(self, obj):
        """Get service tracking information for this inventory item"""
        from warranty_and_services.models import Installation, ServiceFollowUp, MaintenanceRecord
        from django.utils import timezone
        
        try:
            installation = Installation.objects.get(inventory_item=obj)
            
            # Get service follow-ups for this installation
            service_followups = ServiceFollowUp.objects.filter(
                installation=installation
            ).order_by('-next_service_date')
            
            now = timezone.now()
            service_info = {
                'installation_id': installation.id,
                'total_services': service_followups.count(),
                'active_services': [],
                'overdue_services': [],
                'completed_services': [],
                'maintenance_history': [],
                'next_service_date': None,
                'service_status': 'no_service'
            }
            
            # Process service follow-ups
            for followup in service_followups:
                service_data = {
                    'id': followup.id,
                    'service_type': followup.service_type,
                    'service_type_display': followup.get_service_type_display(),
                    'service_value': followup.service_value,
                    'next_service_date': followup.next_service_date,
                    'is_completed': followup.is_completed,
                    'completed_date': followup.completed_date,
                    'calculation_notes': followup.calculation_notes
                }
                
                if followup.is_completed:
                    service_info['completed_services'].append(service_data)
                elif followup.next_service_date <= now:
                    service_info['overdue_services'].append(service_data)
                else:
                    service_info['active_services'].append(service_data)
            
            # Get maintenance records
            maintenance_records = MaintenanceRecord.objects.filter(
                service_followup__installation=installation
            ).select_related('technician').order_by('-maintenance_date')[:5]
            
            for record in maintenance_records:
                maintenance_data = {
                    'id': record.id,
                    'maintenance_type': record.maintenance_type,
                    'maintenance_type_display': record.get_maintenance_type_display(),
                    'service_date': record.service_date,
                    'maintenance_date': record.maintenance_date,
                    'technician_name': f"{record.technician.first_name} {record.technician.last_name}".strip() if record.technician else None,
                    'breakdown_reason': record.breakdown_reason,
                    'notes': record.notes
                }
                service_info['maintenance_history'].append(maintenance_data)
            
            # Determine service status and next service date
            if service_info['overdue_services']:
                service_info['service_status'] = 'overdue'
                service_info['next_service_date'] = min(s['next_service_date'] for s in service_info['overdue_services'])
            elif service_info['active_services']:
                service_info['service_status'] = 'scheduled'
                service_info['next_service_date'] = min(s['next_service_date'] for s in service_info['active_services'])
            elif service_info['completed_services']:
                service_info['service_status'] = 'completed'
            
            # Summary counts
            service_info['summary'] = {
                'total_active': len(service_info['active_services']),
                'total_overdue': len(service_info['overdue_services']),
                'total_completed': len(service_info['completed_services']),
                'total_maintenance': len(service_info['maintenance_history'])
            }
            
            return service_info
            
        except Installation.DoesNotExist:
            return {
                'installation_id': None,
                'total_services': 0,
                'active_services': [],
                'overdue_services': [],
                'completed_services': [],
                'maintenance_history': [],
                'next_service_date': None,
                'service_status': 'not_installed',
                'summary': {
                    'total_active': 0,
                    'total_overdue': 0,
                    'total_completed': 0,
                    'total_maintenance': 0
                }
            }


# Installation serializers
class InstallationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Installation
        fields = [
            'customer', 'inventory_item', 'setup_date',
            'location_latitude', 'location_longitude',
            'location_address', 'installation_notes'
        ]
    
    def create(self, validated_data):
        # Set the user from the logged-in user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class InstallationSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    inventory_item = InventoryItemSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Installation
        fields = [
            'id', 'customer', 'inventory_item', 'user', 'setup_date',
            'location_latitude', 'location_longitude', 'location_address',
            'installation_notes', 'created_at', 'updated_at'
        ]


# Service serializers
class ServiceFollowUpCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFollowUp
        fields = [
            'installation', 'service_type', 'service_value',
            'calculation_notes', 'completion_notes'
        ]


class ServiceFollowUpSerializer(serializers.ModelSerializer):
    installation = InstallationSerializer(read_only=True)
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    
    class Meta:
        model = ServiceFollowUp
        fields = [
            'id', 'installation', 'service_type', 'service_type_display', 
            'service_value', 'next_service_date', 'is_completed', 
            'completed_date', 'calculation_notes', 'completion_notes',
            'created_at', 'updated_at'
        ]


# Maintenance serializers
class MaintenanceRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRecord
        fields = [
            'service_followup', 'maintenance_type', 'technician', 
            'breakdown_reason', 'notes', 'service_date'
        ]


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    service_followup = ServiceFollowUpSerializer(read_only=True)
    technician_name = serializers.SerializerMethodField()
    maintenance_type_display = serializers.CharField(source='get_maintenance_type_display', read_only=True)
    
    class Meta:
        model = MaintenanceRecord
        fields = [
            'id', 'service_followup', 'maintenance_type', 'maintenance_type_display',
            'technician', 'technician_name', 'breakdown_reason', 'notes', 
            'service_date', 'maintenance_date', 'created_at', 'updated_at'
        ]
    
    def get_technician_name(self, obj):
        if obj.technician:
            return f"{obj.technician.first_name} {obj.technician.last_name}".strip()
        return None


# Search response serializer
class SearchResponseSerializer(serializers.Serializer):
    installations = InstallationSerializer(many=True)
    customers = CustomerSerializer(many=True)
    items = ItemMasterSerializer(many=True)
