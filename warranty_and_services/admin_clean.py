# Admin configuration for warranty and services app
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django import forms
from django.utils.html import format_html
from django.db.models import Q
from .models import (
    Installation, WarrantyFollowUp, ServiceFollowUp, 
    InstallationImage, InstallationDocument, ServiceFormEntry,
    ServiceFormEntryImage, ServiceFormEntryDocument
)


# Installation ForeignKey için özel gösterim
class InstallationChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if obj.inventory_item and obj.inventory_item.name:
            return f"{obj.inventory_item.name.name} ({obj.inventory_item.serial_no}) - {obj.customer.name}"
        return str(obj)


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
        widgets = {
            'setup_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default date to today if creating new installation
        if not self.instance.pk and 'setup_date' in self.fields:
            from django.utils import timezone
            self.fields['setup_date'].initial = timezone.now().date()
        
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
    formfield_overrides = {
        # Installation ForeignKey için özel gösterim
        ServiceFollowUp._meta.get_field('installation'): {'form_class': InstallationChoiceField},
    }
    list_display = ['get_installation_item', 'service_type', 'service_value', 'next_service_date', 'is_completed', 'is_due', 'days_until_due']
    def get_installation_item(self, obj):
        if obj.installation and obj.installation.inventory_item and obj.installation.inventory_item.name:
            return f"{obj.installation.inventory_item.name.name} ({obj.installation.inventory_item.serial_no})"
        return str(obj.installation)
    get_installation_item.short_description = _('Installed Item')
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
        created_count = 0
        for service in queryset:
            if not service.is_completed:
                service.complete_and_create_next()
                created_count += 1
        self.message_user(request, f"{created_count} service(s) marked as completed and next service created.")
    mark_completed.short_description = _('Mark selected services as completed and create next')


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


# ServiceFormEntry Admin Configuration
class ServiceFormEntryImageInline(admin.TabularInline):
    """Inline admin for service form entry images"""
    model = ServiceFormEntryImage
    extra = 1
    fields = ['image', 'title']
    readonly_fields = ['uploaded_at']


class ServiceFormEntryDocumentInline(admin.TabularInline):
    """Inline admin for service form entry documents"""
    model = ServiceFormEntryDocument
    extra = 1
    fields = ['document', 'title']
    readonly_fields = ['uploaded_at']


@admin.register(ServiceFormEntry)
class ServiceFormEntryAdmin(admin.ModelAdmin):
    inlines = [ServiceFormEntryImageInline, ServiceFormEntryDocumentInline]
    list_display = ['get_installation_display', 'service_type', 'service_date', 'service_time', 'created_by', 'created_at']
    list_filter = ['service_type', 'service_date', 'created_at', 'created_by']
    search_fields = ['installation__inventory_item__name__name', 'installation__customer__name', 'notes']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (_('Service Details'), {
            'fields': ('installation', 'service_followup', 'service_type', 'service_date', 'service_time')
        }),
        (_('Service Actions'), {
            'fields': ('checked_controls', 'changed_spare_parts', 'notes')
        }),
        (_('Meta Information'), {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def get_installation_display(self, obj):
        if obj.installation and obj.installation.inventory_item:
            return f"{obj.installation.inventory_item.name.name} - {obj.installation.customer.name}"
        return "-"
    get_installation_display.short_description = _('Installation')

    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ServiceFormEntryImage)
class ServiceFormEntryImageAdmin(admin.ModelAdmin):
    list_display = ['get_service_entry_display', 'title', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['service_form_entry__installation__customer__name', 'title']
    readonly_fields = ['uploaded_at']

    def get_service_entry_display(self, obj):
        if obj.service_form_entry and obj.service_form_entry.installation:
            return f"{obj.service_form_entry.installation.customer.name} - {obj.service_form_entry.service_date}"
        return "-"
    get_service_entry_display.short_description = _('Service Entry')


@admin.register(ServiceFormEntryDocument)
class ServiceFormEntryDocumentAdmin(admin.ModelAdmin):
    list_display = ['get_service_entry_display', 'title', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['service_form_entry__installation__customer__name', 'title']
    readonly_fields = ['uploaded_at']

    def get_service_entry_display(self, obj):
        if obj.service_form_entry and obj.service_form_entry.installation:
            return f"{obj.service_form_entry.installation.customer.name} - {obj.service_form_entry.service_date}"
        return "-"
    get_service_entry_display.short_description = _('Service Entry')
