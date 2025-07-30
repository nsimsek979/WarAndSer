from django.contrib import admin
from django import forms
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from import_export.formats.base_formats import CSV, JSON, HTML, TSV, XLSX
from .models import (
    Status, StockType, Brand, Category, ItemImage, ItemSpec,
    WarrantyType, WarrantyValue, ServiceForm, ItemSparePart, ItemMaster,
    AttributeType, AttributeUnit, AttributeTypeUnit, InventoryItem, InventoryItemAttribute,
    ServicePeriodType, ServicePeriodValue, MaintenanceSchedule
)


class InventoryItemAttributeForm(forms.ModelForm):
    class Meta:
        model = InventoryItemAttribute
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If attribute_type is already selected, filter units
        if 'attribute_type' in self.data:
            try:
                attribute_type_id = int(self.data.get('attribute_type'))
                self.fields['unit'].queryset = AttributeUnit.objects.filter(
                    unit_types__attribute_type_id=attribute_type_id
                ).order_by('unit_types__is_default', 'name')
            except (ValueError, TypeError):
                self.fields['unit'].queryset = AttributeUnit.objects.none()
        elif self.instance.pk and self.instance.attribute_type:
            self.fields['unit'].queryset = AttributeUnit.objects.filter(
                unit_types__attribute_type=self.instance.attribute_type
            ).order_by('unit_types__is_default', 'name')
        else:
            self.fields['unit'].queryset = AttributeUnit.objects.none()
        
        # Add CSS classes for dynamic filtering
        self.fields['attribute_type'].widget.attrs.update({
            'class': 'attribute-type-select',
            'data-url': '/admin/get-attribute-units/'  # We'll create this view
        })
        self.fields['unit'].widget.attrs.update({
            'class': 'attribute-unit-select'
        })
    
    def clean(self):
        cleaned_data = super().clean()
        attribute_type = cleaned_data.get('attribute_type')
        unit = cleaned_data.get('unit')
        
        if unit and attribute_type:
            # Check if the unit is compatible with the attribute type
            if not AttributeTypeUnit.objects.filter(
                attribute_type=attribute_type,
                attribute_unit=unit
            ).exists():
                available_units = AttributeUnit.objects.filter(
                    unit_types__attribute_type=attribute_type
                ).values_list('name', flat=True)
                
                raise forms.ValidationError({
                    'unit': f'Unit "{unit.name}" is not compatible with attribute type "{attribute_type.name}". '
                           f'Available units: {", ".join(available_units) if available_units else "None"}'
                })
        
        return cleaned_data


# Inline classes for ItemMaster
class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1
    fields = ('url',)


class ItemSpecInline(admin.TabularInline):
    model = ItemSpec
    extra = 1
    fields = ('url',)


class ItemSparePartInline(admin.TabularInline):
    model = ItemSparePart
    fk_name = 'main_item'  # Specify which foreign key to use
    extra = 1
    fields = ('spare_part_item',)
    verbose_name = "Spare Part"
    verbose_name_plural = "Spare Parts"
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Filter the queryset for spare_part_item field
        try:
            spare_part_stock_type = StockType.objects.get(name="Yedek Parça")
            formset.form.base_fields['spare_part_item'].queryset = ItemMaster.objects.filter(stock_type=spare_part_stock_type)
        except StockType.DoesNotExist:
            formset.form.base_fields['spare_part_item'].queryset = ItemMaster.objects.none()
        return formset


class ItemUsedAsSparePartInline(admin.TabularInline):
    """Shows where this item is used as a spare part"""
    model = ItemSparePart
    fk_name = 'spare_part_item'  # This item is the spare part
    extra = 0
    fields = ('main_item',)
    verbose_name = "Used as spare part for"
    verbose_name_plural = "Used as spare part for"
    
    def has_add_permission(self, request, obj=None):
        return False  # Don't allow adding from this inline
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Filter the queryset for main_item field
        try:
            main_item_stock_type = StockType.objects.get(name="Ticari")
            formset.form.base_fields['main_item'].queryset = ItemMaster.objects.filter(stock_type=main_item_stock_type)
        except StockType.DoesNotExist:
            formset.form.base_fields['main_item'].queryset = ItemMaster.objects.none()
        return formset


class MaintenanceScheduleInline(admin.TabularInline):
    """Inline for managing maintenance schedules in ItemMaster"""
    model = MaintenanceSchedule
    extra = 1
    fields = ('service_period_value', 'is_critical', 'maintenance_description')
    verbose_name = "Bakım Programı"
    verbose_name_plural = "Bakım Programları"


# Inline classes for InventoryItem
class InventoryItemAttributeInline(admin.TabularInline):
    model = InventoryItemAttribute
    form = InventoryItemAttributeForm
    extra = 1
    fields = ('attribute_type', 'value', 'unit', 'notes')
    autocomplete_fields = ['attribute_type']
    verbose_name = "Attribute"
    verbose_name_plural = "Attributes"
    
    class Media:
        js = ('admin/js/attribute_unit_filter.js',)


class InventoryItemInline(admin.TabularInline):
    model = InventoryItem
    fk_name = 'name'  # Specify which foreign key to use
    extra = 0
    fields = ('serial_no', 'production_date', 'in_used')
   
    verbose_name = "Inventory Item"
    verbose_name_plural = "Inventory Items"


class InventoryItemInline(admin.TabularInline):
    model = InventoryItem
    fk_name = 'name'  # Specify which foreign key to use
    extra = 0
    fields = ('serial_no', 'production_date', 'in_used')
   
    verbose_name = "Inventory Item"
    verbose_name_plural = "Inventory Items"


# Import/Export Resources
class StatusResource(resources.ModelResource):
    class Meta:
        model = Status
        fields = ('status',)


class StockTypeResource(resources.ModelResource):
    class Meta:
        model = StockType
        fields = ('name',)


class BrandResource(resources.ModelResource):
    class Meta:
        model = Brand
        fields = ('name',)


class CategoryResource(resources.ModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ForeignKeyWidget(Category, 'category_name')
    )
    
    class Meta:
        model = Category
        fields = ('category_name', 'parent', 'slug')


class ItemMasterResource(resources.ModelResource):
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(Category, 'category_name')
    )
    status = fields.Field(
        column_name='status',
        attribute='status',
        widget=ForeignKeyWidget(Status, 'status')
    )
    brand_name = fields.Field(
        column_name='brand_name',
        attribute='brand_name',
        widget=ForeignKeyWidget(Brand, 'name')
    )
    stock_type = fields.Field(
        column_name='stock_type',
        attribute='stock_type',
        widget=ForeignKeyWidget(StockType, 'name')
    )
    
    class Meta:
        model = ItemMaster
        fields = ('shortcode', 'name', 'description', 'category', 'status', 'brand_name', 'stock_type')


class InventoryItemResource(resources.ModelResource):
    name = fields.Field(
        column_name='item_name',
        attribute='name',
        widget=ForeignKeyWidget(ItemMaster, 'name')
    )
    
    class Meta:
        model = InventoryItem
        fields = ('name', 'serial_no', 'production_date', 'in_used')


class ItemSparePartResource(resources.ModelResource):
    main_item = fields.Field(
        column_name='main_item',
        attribute='main_item',
        widget=ForeignKeyWidget(ItemMaster, 'name')
    )
    spare_part_item = fields.Field(
        column_name='spare_part_item',
        attribute='spare_part_item',
        widget=ForeignKeyWidget(ItemMaster, 'name')
    )
    
    class Meta:
        model = ItemSparePart
        fields = ('main_item', 'spare_part_item')


# Admin classes
@admin.register(Status)
class StatusAdmin(ImportExportModelAdmin):
    resource_class = StatusResource
    list_display = ('status', 'created_at', 'updated_at')
    search_fields = ('status',)
    list_filter = ('created_at',)


@admin.register(StockType)
class StockTypeAdmin(ImportExportModelAdmin):
    resource_class = StockTypeResource
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at',)


@admin.register(Brand)
class BrandAdmin(ImportExportModelAdmin):
    resource_class = BrandResource
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    fields = ('name', 'image')


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    resource_class = CategoryResource
    list_display = ('category_name', 'parent', 'slug', 'created_at')
    list_filter = ('parent', 'created_at')
    search_fields = ('category_name',)
    prepopulated_fields = {'slug': ('category_name',)}
    fields = ('category_name', 'parent', 'slug')


@admin.register(WarrantyType)
class WarrantyTypeAdmin(admin.ModelAdmin):
    list_display = ('type', 'created_at', 'updated_at')
    search_fields = ('type',)
    list_filter = ('created_at',)


@admin.register(WarrantyValue)
class WarrantyValueAdmin(admin.ModelAdmin):
    list_display = ('warranty_type', 'value', 'created_at', 'updated_at')
    list_filter = ('warranty_type', 'created_at')
    search_fields = ('warranty_type__type',)


@admin.register(ServiceForm)
class ServiceFormAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at',)


@admin.register(ServicePeriodType)
class ServicePeriodTypeAdmin(admin.ModelAdmin):
    list_display = ('type', 'unit', 'created_at', 'updated_at')
    search_fields = ('type', 'unit')
    list_filter = ('created_at',)
    fields = ('type', 'unit')


@admin.register(ServicePeriodValue)
class ServicePeriodValueAdmin(admin.ModelAdmin):
    list_display = ('service_period_type', 'value', 'description', 'created_at', 'updated_at')
    list_filter = ('service_period_type', 'created_at')
    search_fields = ('service_period_type__type', 'description')
    fields = ('service_period_type', 'value', 'description')


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ('item_master', 'service_period_value', 'is_critical', 'created_at')
    list_filter = ('is_critical', 'service_period_value__service_period_type', 'created_at')
    search_fields = ('item_master__name', 'item_master__shortcode', 'maintenance_description')
    fields = ('item_master', 'service_period_value', 'is_critical', 'maintenance_description')


@admin.register(AttributeType)
class AttributeTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_required', 'created_at', 'updated_at')
    list_filter = ('is_required', 'created_at')
    search_fields = ('name', 'description')
    fields = ('name', 'description', 'is_required')


@admin.register(AttributeTypeUnit)
class AttributeTypeUnitAdmin(admin.ModelAdmin):
    list_display = ('attribute_type', 'attribute_unit', 'is_default', 'created_at')
    list_filter = ('attribute_type', 'is_default', 'created_at')
    search_fields = ('attribute_type__name', 'attribute_unit__name', 'attribute_unit__symbol')
    fields = ('attribute_type', 'attribute_unit', 'is_default')
    autocomplete_fields = ['attribute_type', 'attribute_unit']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Add help text
        form.base_fields['is_default'].help_text = "Only one unit can be default per attribute type"
        return form


@admin.register(AttributeUnit)
class AttributeUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'get_attribute_types', 'created_at', 'updated_at')
    search_fields = ('name', 'symbol')
    list_filter = ('created_at',)
    fields = ('name', 'symbol')
    
    def get_attribute_types(self, obj):
        types = obj.unit_types.values_list('attribute_type__name', flat=True)
        return ", ".join(types) if types else "No types assigned"
    get_attribute_types.short_description = 'Attribute Types'


@admin.register(ItemSparePart)
class ItemSparePartAdmin(ImportExportModelAdmin):
    resource_class = ItemSparePartResource
    list_display = ('main_item_code', 'main_item_name', 'spare_part_code', 'spare_part_name', 'created_at')
    list_filter = ('created_at', 'main_item__stock_type', 'spare_part_item__stock_type')
    search_fields = ('main_item__shortcode', 'main_item__name', 'spare_part_item__shortcode', 'spare_part_item__name')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Filter the querysets for both fields
        try:
            spare_part_stock_type = StockType.objects.get(name="Yedek Parça")
            main_item_stock_type = StockType.objects.get(name="Ticari")
            form.base_fields['spare_part_item'].queryset = ItemMaster.objects.filter(stock_type=spare_part_stock_type)
            form.base_fields['main_item'].queryset = ItemMaster.objects.filter(stock_type=main_item_stock_type)
        except StockType.DoesNotExist:
            form.base_fields['spare_part_item'].queryset = ItemMaster.objects.none()
            form.base_fields['main_item'].queryset = ItemMaster.objects.none()
        return form
    
    def main_item_code(self, obj):
        return obj.main_item.shortcode
    main_item_code.short_description = 'Main Item Code'
    
    def main_item_name(self, obj):
        return obj.main_item.name
    main_item_name.short_description = 'Main Item Name'
    
    def spare_part_code(self, obj):
        return obj.spare_part_item.shortcode
    spare_part_code.short_description = 'Spare Part Code'
    
    def spare_part_name(self, obj):
        return obj.spare_part_item.name
    spare_part_name.short_description = 'Spare Part Name'


@admin.register(ItemMaster)
class ItemMasterAdmin(ImportExportModelAdmin):
    resource_class = ItemMasterResource
    list_display = ('shortcode', 'name', 'category', 'brand_name', 'status', 'stock_type', 'created_at')
    list_filter = ('category', 'brand_name', 'status', 'stock_type', 'created_at')
    search_fields = ('shortcode', 'name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('warranties', 'service_forms')  # For M2M fields
    autocomplete_fields = ['category', 'status', 'brand_name', 'stock_type']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('shortcode', 'name', 'description', 'slug')
        }),
        ('Classification', {
            'fields': ('category', 'status', 'brand_name', 'stock_type')
        }),
        ('Warranties & Services', {
            'fields': ('warranties', 'service_forms'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ItemImageInline, ItemSpecInline, ItemSparePartInline, ItemUsedAsSparePartInline, MaintenanceScheduleInline, InventoryItemInline]


@admin.register(InventoryItem)
class InventoryItemAdmin(ImportExportModelAdmin):
    resource_class = InventoryItemResource
    list_display = ('item_name', 'serial_no', 'production_date', 'in_used', 'created_by', 'created_at')
    list_filter = ('in_used', 'name__category', 'name__brand_name', 'created_at', 'production_date')
    search_fields = ('serial_no', 'name__name', 'name__shortcode')
    readonly_fields = ('qr_code_image', 'qr_code_preview', 'production_date', 'created_at')
    autocomplete_fields = ['name', 'created_by']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'serial_no')
        }),
        ('Dates & Status', {
            'fields': ('production_date', 'in_used', 'created_by')
        }),
        ('QR Code', {
            'fields': ('qr_code_image', 'qr_code_preview'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [InventoryItemAttributeInline]
    
    def item_name(self, obj):
        return obj.name.name
    item_name.short_description = 'Item Name'
    
    def qr_code_preview(self, obj):
        if obj.qr_code_image:
            return f'<img src="{obj.qr_code_image.url}" style="max-width: 200px; max-height: 200px;">'
        return "No QR code"
    qr_code_preview.short_description = 'QR Code Preview'
    qr_code_preview.allow_tags = True


@admin.register(InventoryItemAttribute)
class InventoryItemAttributeAdmin(admin.ModelAdmin):
    form = InventoryItemAttributeForm
    list_display = ('inventory_item_code', 'attribute_type', 'value', 'unit', 'created_at')
    list_filter = ('attribute_type', 'unit', 'created_at')
    search_fields = ('inventory_item__item_code', 'attribute_type__name', 'value')
    autocomplete_fields = ['inventory_item', 'attribute_type']
    
    fieldsets = (
        ('Attribute Information', {
            'fields': ('inventory_item', 'attribute_type', 'value', 'unit')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def inventory_item_code(self, obj):
        return obj.inventory_item.name.shortcode if obj.inventory_item else "No Item"
    inventory_item_code.short_description = 'Inventory Item Code'


# Register remaining models without custom admin
admin.site.register(ItemImage)
admin.site.register(ItemSpec)