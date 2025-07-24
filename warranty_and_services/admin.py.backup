

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



 
 
 #   S e r v i c e F o r m E n t r y   A d m i n   C o n f i g u r a t i o n 
 c l a s s   S e r v i c e F o r m E n t r y I m a g e I n l i n e ( a d m i n . T a b u l a r I n l i n e ) : 
         m o d e l   =   S e r v i c e F o r m E n t r y I m a g e 
         e x t r a   =   1 
         f i e l d s   =   [ ' i m a g e ' ,   ' t i t l e ' ] 
         r e a d o n l y _ f i e l d s   =   [ ' u p l o a d e d _ a t ' ] 
 
 
 c l a s s   S e r v i c e F o r m E n t r y D o c u m e n t I n l i n e ( a d m i n . T a b u l a r I n l i n e ) : 
         m o d e l   =   S e r v i c e F o r m E n t r y D o c u m e n t 
         e x t r a   =   1 
         f i e l d s   =   [ ' d o c u m e n t ' ,   ' t i t l e ' ] 
         r e a d o n l y _ f i e l d s   =   [ ' u p l o a d e d _ a t ' ] 
 
 
 @ a d m i n . r e g i s t e r ( S e r v i c e F o r m E n t r y ) 
 c l a s s   S e r v i c e F o r m E n t r y A d m i n ( a d m i n . M o d e l A d m i n ) : 
         i n l i n e s   =   [ S e r v i c e F o r m E n t r y I m a g e I n l i n e ,   S e r v i c e F o r m E n t r y D o c u m e n t I n l i n e ] 
         l i s t _ d i s p l a y   =   [ ' g e t _ i n s t a l l a t i o n _ d i s p l a y ' ,   ' s e r v i c e _ t y p e ' ,   ' s e r v i c e _ d a t e ' ,   ' s e r v i c e _ t i m e ' ,   ' c r e a t e d _ b y ' ,   ' c r e a t e d _ a t ' ] 
         l i s t _ f i l t e r   =   [ ' s e r v i c e _ t y p e ' ,   ' s e r v i c e _ d a t e ' ,   ' c r e a t e d _ a t ' ,   ' c r e a t e d _ b y ' ] 
         s e a r c h _ f i e l d s   =   [ ' i n s t a l l a t i o n _ _ i n v e n t o r y _ i t e m _ _ n a m e _ _ n a m e ' ,   ' i n s t a l l a t i o n _ _ c u s t o m e r _ _ n a m e ' ,   ' n o t e s ' ] 
         r e a d o n l y _ f i e l d s   =   [ ' c r e a t e d _ a t ' ] 
         
         f i e l d s e t s   =   ( 
                 ( _ ( ' S e r v i c e   D e t a i l s ' ) ,   { 
                         ' f i e l d s ' :   ( ' i n s t a l l a t i o n ' ,   ' s e r v i c e _ f o l l o w u p ' ,   ' s e r v i c e _ t y p e ' ,   ' s e r v i c e _ d a t e ' ,   ' s e r v i c e _ t i m e ' ) 
                 } ) , 
                 ( _ ( ' S e r v i c e   A c t i o n s ' ) ,   { 
                         ' f i e l d s ' :   ( ' c h e c k e d _ c o n t r o l s ' ,   ' c h a n g e d _ s p a r e _ p a r t s ' ,   ' n o t e s ' ) 
                 } ) , 
                 ( _ ( ' M e t a   I n f o r m a t i o n ' ) ,   { 
                         ' f i e l d s ' :   ( ' c r e a t e d _ b y ' ,   ' c r e a t e d _ a t ' ) , 
                         ' c l a s s e s ' :   ( ' c o l l a p s e ' , ) 
                 } ) , 
         ) 
 
         d e f   g e t _ i n s t a l l a t i o n _ d i s p l a y ( s e l f ,   o b j ) : 
                 i f   o b j . i n s t a l l a t i o n   a n d   o b j . i n s t a l l a t i o n . i n v e n t o r y _ i t e m : 
                         r e t u r n   f \ 
 
 o b j . i n s t a l l a t i o n . i n v e n t o r y _ i t e m . n a m e . n a m e 
 
 - 
 
 o b j . i n s t a l l a t i o n . c u s t o m e r . n a m e 
 
 \ 
                 r e t u r n   \ - \ 
         g e t _ i n s t a l l a t i o n _ d i s p l a y . s h o r t _ d e s c r i p t i o n   =   _ ( ' I n s t a l l a t i o n ' ) 
 
         d e f   s a v e _ m o d e l ( s e l f ,   r e q u e s t ,   o b j ,   f o r m ,   c h a n g e ) : 
                 i f   n o t   c h a n g e : 
                         o b j . c r e a t e d _ b y   =   r e q u e s t . u s e r 
                 s u p e r ( ) . s a v e _ m o d e l ( r e q u e s t ,   o b j ,   f o r m ,   c h a n g e ) 
 
 
 