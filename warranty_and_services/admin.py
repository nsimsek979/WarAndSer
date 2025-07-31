from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django import forms
from django.db.models import Q
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, DateTimeWidget
from django.utils import timezone
from .models import Installation, WarrantyFollowUp, ServiceFollowUp, InstallationImage, InstallationDocument, BreakdownReason, BreakdownCategory, MaintenanceRecord

class NaiveDateTimeWidget(DateTimeWidget):
    """Custom widget to remove timezone info from datetime objects for Excel export"""
    def render(self, value, obj=None, **kwargs):
        if value and hasattr(value, 'replace'):
            # Remove timezone info
            value = value.replace(tzinfo=None)
        return super().render(value, obj, **kwargs)


class InstallationImageInline(admin.TabularInline):
    """Inline admin for installation images"""
    model = InstallationImage
    extra = 1
    fields = ['image', 'title', 'image_type', 'description']
    readonly_fields = ['file_size_display', 'captured_at']


class InstallationDocumentInline(admin.TabularInline):
    """Inline admin for installation documents"""
    model = InstallationDocument
    extra = 1
    fields = ['document', 'title', 'document_type', 'is_required', 'is_confidential']
    readonly_fields = ['file_size_display', 'file_extension', 'uploaded_at']


class InstallationAdminForm(forms.ModelForm):
    """Custom form for Installation to improve inventory item display"""
    
    class Meta:
        model = Installation
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Improve inventory item queryset and display
        if 'inventory_item' in self.fields:
            from item_master.models import InventoryItem
            
            # If editing existing installation, include current item even if in_used=True
            if self.instance and self.instance.pk and self.instance.inventory_item:
                current_item = self.instance.inventory_item
                available_items = InventoryItem.objects.filter(
                    Q(in_used=False) | Q(pk=current_item.pk)
                ).select_related('name').order_by('name__shortcode', 'serial_no')
            else:
                # For new installations, only show available items
                available_items = InventoryItem.objects.filter(
                    in_used=False
                ).select_related('name').order_by('name__shortcode', 'serial_no')
            
            self.fields['inventory_item'].queryset = available_items
            
            # Improve display of choices
            self.fields['inventory_item'].label_from_instance = lambda obj: f"{obj.name.shortcode} - {obj.serial_no} ({'In Use' if obj.in_used else 'Available'})"


# Import/Export Resources
class BreakdownCategoryResource(resources.ModelResource):
    class Meta:
        model = BreakdownCategory
        fields = ('name', 'description', 'is_active')
        exclude = ('id',)


class BreakdownReasonResource(resources.ModelResource):
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(BreakdownCategory, 'name')
    )
    
    class Meta:
        model = BreakdownReason
        fields = ('name', 'category', 'description', 'is_active')
        exclude = ('id',)


class InstallationResource(resources.ModelResource):
    inventory_item_shortcode = fields.Field(
        column_name='inventory_item_shortcode',
        attribute='inventory_item__name__shortcode'
    )
    inventory_item_serial = fields.Field(
        column_name='inventory_item_serial',
        attribute='inventory_item__serial_no'
    )
    customer_name = fields.Field(
        column_name='customer_name',
        attribute='customer__name'
    )
    installer = fields.Field(
        column_name='installer',
        attribute='user__username'
    )
    
    class Meta:
        model = Installation
        fields = ('setup_date', 'inventory_item_shortcode', 'inventory_item_serial', 'customer_name', 'installer', 'location_latitude', 'location_longitude', 'location_address', 'installation_notes')
        exclude = ('id',)


class WarrantyFollowUpResource(resources.ModelResource):
    installation_equipment = fields.Field(
        column_name='installation_equipment',
        attribute='installation__inventory_item__name__shortcode'
    )
    installation_serial = fields.Field(
        column_name='installation_serial',
        attribute='installation__inventory_item__serial_no'
    )
    customer_name = fields.Field(
        column_name='customer_name',
        attribute='installation__customer__name'
    )
    
    class Meta:
        model = WarrantyFollowUp
        fields = ('installation_equipment', 'installation_serial', 'customer_name', 'warranty_type', 'warranty_start', 'warranty_end', 'is_active')
        exclude = ('id',)


class ServiceFollowUpResource(resources.ModelResource):
    installation_equipment = fields.Field(
        column_name='installation_equipment',
        attribute='installation__inventory_item__name__shortcode'
    )
    installation_serial = fields.Field(
        column_name='installation_serial',
        attribute='installation__inventory_item__serial_no'
    )
    customer_name = fields.Field(
        column_name='customer_name',
        attribute='installation__customer__name'
    )
    
    class Meta:
        model = ServiceFollowUp
        fields = ('installation_equipment', 'installation_serial', 'customer_name', 'service_type', 'next_service_date', 'service_value', 'is_completed')
        exclude = ('id',)


class MaintenanceRecordResource(resources.ModelResource):
    installation_equipment = fields.Field(
        column_name='installation_equipment',
        attribute='installation__inventory_item__name__shortcode'
    )
    installation_serial = fields.Field(
        column_name='installation_serial',
        attribute='installation__inventory_item__serial_no'
    )
    customer_name = fields.Field(
        column_name='customer_name',
        attribute='installation__customer__name'
    )
    breakdown_category = fields.Field(
        column_name='breakdown_category',
        attribute='breakdown_category__name'
    )
    breakdown_reason = fields.Field(
        column_name='breakdown_reason',
        attribute='breakdown_reason__name'
    )
    technician = fields.Field(
        column_name='technician',
        attribute='technician__username'
    )
    
    class Meta:
        model = MaintenanceRecord
        fields = ('installation_equipment', 'installation_serial', 'customer_name', 'maintenance_type', 'breakdown_category', 'breakdown_reason', 'technician', 'maintenance_date', 'breakdown_details', 'notes')
        exclude = ('id',)


@admin.register(Installation)
class InstallationAdmin(ImportExportModelAdmin):
    resource_class = InstallationResource
    form = InstallationAdminForm
    list_display = ['get_inventory_display', 'get_customer_display', 'setup_date', 'user', 'has_location']
    list_filter = ['setup_date', 'user', 'customer__company_type']
    search_fields = ['inventory_item__name__name', 'inventory_item__serial_no', 'customer__name', 'installation_notes']
    inlines = [InstallationImageInline, InstallationDocumentInline]
    date_hierarchy = 'setup_date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Installation Details'), {
            'fields': ('user', 'setup_date', 'inventory_item', 'customer')
        }),
        (_('Location Information'), {
            'fields': ('location_latitude', 'location_longitude', 'location_address'),
            'classes': ('collapse',)
        }),
        (_('Notes'), {
            'fields': ('installation_notes',),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_inventory_display(self, obj):
        if obj.inventory_item:
            return f"{obj.inventory_item.name.shortcode} - {obj.inventory_item.serial_no}"
        return "-"
    get_inventory_display.short_description = _('Equipment')

    def get_customer_display(self, obj):
        if obj.customer:
            return obj.customer.name
        return "-"
    get_customer_display.short_description = _('Customer')

    def has_location(self, obj):
        return obj.has_location
    has_location.boolean = True
    has_location.short_description = _('GPS Location')


@admin.register(WarrantyFollowUp)
class WarrantyFollowUpAdmin(ImportExportModelAdmin):
    resource_class = WarrantyFollowUpResource
    list_display = ['get_installation_display', 'warranty_type', 'warranty_value', 'end_of_warranty_date', 'is_active', 'is_expiring_soon']
    list_filter = ['warranty_type', 'end_of_warranty_date']
    search_fields = ['installation__inventory_item__name__name', 'installation__customer__name']
    readonly_fields = ['end_of_warranty_date', 'calculation_notes', 'created_at', 'updated_at']
    date_hierarchy = 'end_of_warranty_date'
    
    fieldsets = (
        (_('Warranty Information'), {
            'fields': ('installation', 'warranty_type', 'warranty_value')
        }),
        (_('Calculated Results'), {
            'fields': ('end_of_warranty_date', 'calculation_notes'),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_installation_display(self, obj):
        if obj.installation:
            return f"{obj.installation.inventory_item.name.shortcode} - {obj.installation.customer.name}"
        return "-"
    get_installation_display.short_description = _('Installation')

    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = _('Active')

    def is_expiring_soon(self, obj):
        return obj.is_expiring_soon
    is_expiring_soon.boolean = True
    is_expiring_soon.short_description = _('Expiring Soon')


@admin.register(ServiceFollowUp)
class ServiceFollowUpAdmin(ImportExportModelAdmin):
    resource_class = ServiceFollowUpResource
    list_display = ['get_installation_display', 'service_type', 'service_value', 'next_service_date', 'is_completed', 'is_due']
    list_filter = ['service_type', 'is_completed', 'next_service_date']
    search_fields = ['installation__inventory_item__name__name', 'installation__customer__name']
    readonly_fields = ['calculation_notes', 'created_at', 'updated_at']
    date_hierarchy = 'next_service_date'
    
    fieldsets = (
        (_('Service Information'), {
            'fields': ('installation', 'service_type', 'service_value', 'next_service_date')
        }),
        (_('Status'), {
            'fields': ('is_completed', 'completed_date', 'completion_notes')
        }),
        (_('Calculated Results'), {
            'fields': ('calculation_notes',),
            'classes': ('collapse',)
        }),
        (_('System Info'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_installation_display(self, obj):
        if obj.installation:
            return f"{obj.installation.inventory_item.name.shortcode} - {obj.installation.customer.name}"
        return "-"
    get_installation_display.short_description = _('Installation')

    def is_due(self, obj):
        return obj.is_due
    is_due.boolean = True
    is_due.short_description = _('Due')


@admin.register(BreakdownCategory)
class BreakdownCategoryAdmin(ImportExportModelAdmin):
    resource_class = BreakdownCategoryResource
    list_display = ['type', 'name', 'is_active', 'created_at']
    list_filter = ['type', 'is_active']
    search_fields = ['name']
    ordering = ['type']
    
    fieldsets = (
        (None, {
            'fields': ('type', 'name', 'is_active')
        }),
    )


@admin.register(BreakdownReason)
class BreakdownReasonAdmin(ImportExportModelAdmin):
    resource_class = BreakdownReasonResource
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'is_active')
        }),
    )


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(ImportExportModelAdmin):
    resource_class = MaintenanceRecordResource
    list_display = ['get_installation_display', 'maintenance_type', 'technician', 'category', 'breakdown_reason_selected', 'service_date', 'created_at']
    list_filter = ['maintenance_type', 'category', 'created_at']
    search_fields = ['service_followup__installation__customer__name', 'technician__first_name', 'technician__last_name', 'notes']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('service_followup', 'maintenance_type', 'technician', 'service_date')
        }),
        (_('Breakdown Information'), {
            'fields': ('category', 'breakdown_reason_selected', 'breakdown_reason_detail'),
            'classes': ('collapse',),
            'description': _('Required for breakdown maintenance only')
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def get_installation_display(self, obj):
        if obj.service_followup and obj.service_followup.installation:
            inst = obj.service_followup.installation
            return f"{inst.inventory_item.name.shortcode} - {inst.customer.name}"
        return "-"
    get_installation_display.short_description = _('Installation')
    
    def save_model(self, request, obj, form, change):
        # Auto-set technician to current user if not set
        if not obj.technician:
            obj.technician = request.user
        super().save_model(request, obj, form, change)
