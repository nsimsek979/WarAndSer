from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django import forms
from django.utils.html import format_html
from django.db.models import Q
from .models import Installation, WarrantyFollowUp, ServiceFollowUp, InstallationImage, InstallationDocument


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
            self.fields['inventory_item'].empty_label = "Select inventory item"


@admin.register(Installation)
class InstallationAdmin(admin.ModelAdmin):
    form = InstallationAdminForm
    inlines = [InstallationImageInline, InstallationDocumentInline]
    list_display = ['get_inventory_display', 'customer', 'user', 'setup_date', 'has_location', 'get_images_count', 'get_documents_count', 'created_at']
    list_filter = ['setup_date', 'user', 'created_at']
    search_fields = ['inventory_item__name__shortcode', 'inventory_item__serial_no', 'customer__name', 'location_address']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Installation Details'), {
            'fields': ('user', 'setup_date', 'inventory_item', 'customer')
        }),
        (_('Location Information'), {
            'fields': ('location_latitude', 'location_longitude', 'location_address'),
            'classes': ('collapse',)
        }),
        (_('Additional Information'), {
            'fields': ('installation_notes',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_location(self, obj):
        return obj.has_location
    has_location.boolean = True
    has_location.short_description = _('Has GPS Location')

    def get_inventory_display(self, obj):
        if obj.inventory_item:
            return f"{obj.inventory_item.name.shortcode} - {obj.inventory_item.serial_no}"
        return "-"
    get_inventory_display.short_description = _('Inventory Item')

    def get_images_count(self, obj):
        count = obj.images.count()
        if count > 0:
            return format_html('<span style="color: green;">📷 {}</span>', count)
        return format_html('<span style="color: gray;">📷 0</span>')
    get_images_count.short_description = _('Images')

    def get_documents_count(self, obj):
        count = obj.documents.count()
        if count > 0:
            return format_html('<span style="color: blue;">📄 {}</span>', count)
        return format_html('<span style="color: gray;">📄 0</span>')
    get_documents_count.short_description = _('Documents')


@admin.register(WarrantyFollowUp)
class WarrantyFollowUpAdmin(admin.ModelAdmin):
    list_display = ['installation', 'warranty_type', 'warranty_value', 'end_of_warranty_date', 'is_active', 'days_remaining']
    list_filter = ['warranty_type', 'end_of_warranty_date', 'created_at']
    search_fields = ['installation__inventory_item__name__name', 'installation__customer__name']
    readonly_fields = ['end_of_warranty_date', 'calculation_notes', 'created_at', 'updated_at']
    
    fieldsets = (
        (_('Warranty Details'), {
            'fields': ('installation', 'warranty_type', 'warranty_value')
        }),
        (_('Calculated Information'), {
            'fields': ('end_of_warranty_date', 'calculation_notes'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = _('Active')

    def days_remaining(self, obj):
        return obj.days_remaining
    days_remaining.short_description = _('Days Remaining')


@admin.register(ServiceFollowUp)
class ServiceFollowUpAdmin(admin.ModelAdmin):
    list_display = ['installation', 'service_type', 'service_value', 'next_service_date', 'is_completed', 'is_due', 'days_until_due']
    list_filter = ['service_type', 'is_completed', 'next_service_date', 'created_at']
    search_fields = ['installation__inventory_item__name__name', 'installation__customer__name']
    readonly_fields = ['next_service_date', 'calculation_notes', 'created_at', 'updated_at']
    
    fieldsets = (
        (_('Service Details'), {
            'fields': ('installation', 'service_type', 'service_value')
        }),
        (_('Service Status'), {
            'fields': ('is_completed', 'completed_date')
        }),
        (_('Calculated Information'), {
            'fields': ('next_service_date', 'calculation_notes'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_due(self, obj):
        return obj.is_due
    is_due.boolean = True
    is_due.short_description = _('Due')

    def days_until_due(self, obj):
        return obj.days_until_due
    days_until_due.short_description = _('Days Until Due')

    actions = ['mark_completed']

    def mark_completed(self, request, queryset):
        for service in queryset:
            service.mark_completed()
        self.message_user(request, f"{queryset.count()} service(s) marked as completed.")
    mark_completed.short_description = _('Mark selected services as completed')


@admin.register(InstallationImage)
class InstallationImageAdmin(admin.ModelAdmin):
    list_display = ['get_installation_display', 'title', 'image_type', 'file_size_display', 'captured_at', 'uploaded_by']
    list_filter = ['image_type', 'captured_at', 'uploaded_by']
    search_fields = ['installation__inventory_item__name__shortcode', 'installation__customer__name', 'title', 'description']
    readonly_fields = ['file_size', 'file_size_display', 'captured_at']
    
    fieldsets = (
        (_('Image Details'), {
            'fields': ('installation', 'image', 'title', 'image_type', 'description')
        }),
        (_('Upload Information'), {
            'fields': ('uploaded_by', 'captured_at', 'file_size_display'),
            'classes': ('collapse',)
        }),
    )

    def get_installation_display(self, obj):
        if obj.installation:
            return f"{obj.installation.inventory_item.name.shortcode} - {obj.installation.customer.name}"
        return "-"
    get_installation_display.short_description = _('Installation')


@admin.register(InstallationDocument)
class InstallationDocumentAdmin(admin.ModelAdmin):
    list_display = ['get_installation_display', 'title', 'document_type', 'file_extension', 'file_size_display', 'is_required', 'is_confidential', 'uploaded_at']
    list_filter = ['document_type', 'is_required', 'is_confidential', 'uploaded_at', 'uploaded_by']
    search_fields = ['installation__inventory_item__name__shortcode', 'installation__customer__name', 'title', 'description']
    readonly_fields = ['file_size', 'file_size_display', 'file_extension', 'uploaded_at']
    
    fieldsets = (
        (_('Document Details'), {
            'fields': ('installation', 'document', 'title', 'document_type', 'description')
        }),
        (_('Document Settings'), {
            'fields': ('is_required', 'is_confidential')
        }),
        (_('Upload Information'), {
            'fields': ('uploaded_by', 'uploaded_at', 'file_extension', 'file_size_display'),
            'classes': ('collapse',)
        }),
    )

    def get_installation_display(self, obj):
        if obj.installation:
            return f"{obj.installation.inventory_item.name.shortcode} - {obj.installation.customer.name}"
        return "-"
    get_installation_display.short_description = _('Installation')
