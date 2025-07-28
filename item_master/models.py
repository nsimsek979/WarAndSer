from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import qrcode
from io import BytesIO
from django.core.files import File

User = get_user_model()

def get_qrcode_upload_path(instance, filename):
    """Generate upload path for QR code images"""
    return f'qrcodes/{instance.id}/{filename}'

class Status(models.Model):
    status = models.CharField(max_length=100, verbose_name=_("Status"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self):
        return self.status

    class Meta:
        verbose_name = _("Status")
        verbose_name_plural = _("Statuses")

class StockType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Stock Type")
        verbose_name_plural = _("Stock Types")

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    image = models.ImageField(upload_to='brands/', null=True, blank=True, verbose_name=_("Image"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Brand")
        verbose_name_plural = _("Brands")

class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True, verbose_name=_("Category Name"))
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, default=None, verbose_name=_("Parent Category"))
    slug = models.SlugField(max_length=100, unique=True, verbose_name=_("Slug"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.category_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

class ItemImage(models.Model):
    item = models.ForeignKey('ItemMaster', on_delete=models.CASCADE, related_name='images', verbose_name=_("Item"))
    url = models.ImageField(upload_to='item_images/', verbose_name=_("Image"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self):
        return f"{self.item.name} - {self.id}"

    class Meta:
        verbose_name = _("Item Image")
        verbose_name_plural = _("Item Images")

class ItemSpec(models.Model):
    item = models.ForeignKey('ItemMaster', on_delete=models.CASCADE, related_name='specs', verbose_name=_("Item"))
    url = models.FileField(upload_to='item_specs/', unique=True, verbose_name=_("Specification File"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self):
        return f"{self.item.name} - {self.id}"

    class Meta:
        verbose_name = _("Item Specification")
        verbose_name_plural = _("Item Specifications")

class WarrantyType(models.Model):
    type = models.CharField(max_length=100, verbose_name=_("Type"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self):
        return self.type

    class Meta:
        verbose_name = _("Warranty Type")
        verbose_name_plural = _("Warranty Types")

class WarrantyValue(models.Model):
    warranty_type = models.ForeignKey(WarrantyType, on_delete=models.CASCADE, verbose_name=_("Warranty Type"))
    value = models.FloatField(verbose_name=_("Value"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self):
        return f"{self.warranty_type}: {self.value}"

    class Meta:
        verbose_name = _("Warranty Value")
        verbose_name_plural = _("Warranty Values")

class ServicePeriodType(models.Model):
    """Servis periyodu türleri (Ay bazlı, Çalışma saati bazlı, vb.)"""
    type = models.CharField(max_length=100, help_text=_("Example: Monthly, Working hours based, Kilometer based"), verbose_name=_("Type"))
    unit = models.CharField(max_length=50, help_text=_("Example: month, hour, km"), verbose_name=_("Unit"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _('Service Period Type')
        verbose_name_plural = _('Service Period Types')

    def __str__(self):
        return f"{self.type} ({self.unit})"

class ServicePeriodValue(models.Model):
    """Servis periyodu değerleri"""
    service_period_type = models.ForeignKey(ServicePeriodType, on_delete=models.CASCADE, verbose_name=_("Service Period Type"))
    value = models.FloatField(help_text=_("Example: 6 months, 3000 hours, 10000 km"), verbose_name=_("Value"))
    description = models.CharField(max_length=200, blank=True, help_text=_("Optional description"), verbose_name=_("Description"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _('Service Period Value')
        verbose_name_plural = _('Service Period Values')

    def __str__(self):
        return f"{self.value} {self.service_period_type.unit} - {self.service_period_type.type}"

class MaintenanceSchedule(models.Model):
    """Ana bakım programı - hangi ürün için hangi servis periyotları geçerli"""
    item_master = models.ForeignKey('ItemMaster', on_delete=models.CASCADE, related_name='maintenance_schedules', verbose_name=_("Item Master"))
    service_period_value = models.ForeignKey(ServicePeriodValue, on_delete=models.CASCADE, verbose_name=_("Service Period Value"))
    is_critical = models.BooleanField(default=True, help_text=_("Is this a critical maintenance?"), verbose_name=_("Is Critical"))
    maintenance_description = models.TextField(blank=True, help_text=_("Maintenance description"), verbose_name=_("Maintenance Description"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _('Maintenance Schedule')
        verbose_name_plural = _('Maintenance Schedules')
        unique_together = ('item_master', 'service_period_value')

    def clean(self):
        """Validate that no duplicate service period types exist for the same item"""
        from django.core.exceptions import ValidationError
        
        if self.item_master and self.service_period_value:
            # Check for existing maintenance schedules with the same service period type
            existing_schedules = MaintenanceSchedule.objects.filter(
                item_master=self.item_master,
                service_period_value__service_period_type=self.service_period_value.service_period_type
            )
            
            # If updating, exclude the current instance
            if self.pk:
                existing_schedules = existing_schedules.exclude(pk=self.pk)
            
            if existing_schedules.exists():
                existing_schedule = existing_schedules.first()
                raise ValidationError({
                    'service_period_value': f'Bu item için "{self.service_period_value.service_period_type.type}" '
                                          f'tipinde zaten bir bakım programı var: '
                                          f'{existing_schedule.service_period_value.value} {existing_schedule.service_period_value.service_period_type.unit}'
                })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_master.name} - {self.service_period_value}"

class ServiceForm(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Service Form")
        verbose_name_plural = _("Service Forms")

class AttributeType(models.Model):
    """Types of attributes that can be assigned to inventory items"""
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    is_required = models.BooleanField(default=False, verbose_name=_("Is Required"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _('Attribute Type')
        verbose_name_plural = _('Attribute Types')
        ordering = ['name']

    def __str__(self):
        return self.name

class AttributeUnit(models.Model):
    """Units of measurement for attributes"""
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Name"))
    symbol = models.CharField(max_length=10, unique=True, verbose_name=_("Symbol"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _('Attribute Unit')
        verbose_name_plural = _('Attribute Units')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class AttributeTypeUnit(models.Model):
    """Relationship between AttributeType and AttributeUnit"""
    attribute_type = models.ForeignKey(
        AttributeType, 
        on_delete=models.CASCADE, 
        related_name='type_units',
        verbose_name=_("Attribute Type")
    )
    attribute_unit = models.ForeignKey(
        AttributeUnit, 
        on_delete=models.CASCADE, 
        related_name='unit_types',
        verbose_name=_("Attribute Unit")
    )
    is_default = models.BooleanField(
        default=False, 
        help_text=_("Is this the default unit for this attribute type?"),
        verbose_name=_("Is Default")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _('Attribute Type Unit')
        verbose_name_plural = _('Attribute Type Units')
        unique_together = ('attribute_type', 'attribute_unit')
        ordering = ['attribute_type__name', '-is_default', 'attribute_unit__name']

    def __str__(self):
        default_text = " (Default)" if self.is_default else ""
        return f"{self.attribute_type.name} - {self.attribute_unit.name}{default_text}"

    def save(self, *args, **kwargs):
        # If this is set as default, remove default from other units of the same type
        if self.is_default:
            AttributeTypeUnit.objects.filter(
                attribute_type=self.attribute_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

class ItemSparePart(models.Model):
    main_item = models.ForeignKey('ItemMaster', on_delete=models.CASCADE, related_name='main_item_spare_parts_set', verbose_name=_("Main Item"))
    spare_part_item = models.ForeignKey('ItemMaster', on_delete=models.CASCADE, related_name='spare_part_of_items_set', verbose_name=_("Spare Part Item"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        unique_together = ('main_item', 'spare_part_item')
        verbose_name = _("Item Spare Part")
        verbose_name_plural = _("Item Spare Parts")

    def __str__(self):
        return f"{self.main_item.name} - {self.spare_part_item.name}"

class ItemMaster(models.Model):
    shortcode = models.CharField(max_length=10, unique=True, verbose_name=_("Short Code"))
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    description = models.TextField(null=True, blank=True, verbose_name=_("Description"))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='items', verbose_name=_("Category"))
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, verbose_name=_("Status"))
    brand_name = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, verbose_name=_("Brand"))
    stock_type = models.ForeignKey(StockType, on_delete=models.SET_NULL, null=True, verbose_name=_("Stock Type"))
    slug = models.SlugField(max_length=255, unique=True, verbose_name=_("Slug"))
    
    spare_parts = models.ManyToManyField(
        "self",
        through='ItemSparePart',
        symmetrical=False,
        blank=True,
        through_fields=('main_item', 'spare_part_item'),
        verbose_name=_("Spare Parts")
    )
    
    warranties = models.ManyToManyField(
        WarrantyValue, 
        blank=True,
        verbose_name=_("Warranties")
    )
    service_forms = models.ManyToManyField(
        ServiceForm, 
        blank=True,
        verbose_name=_("Service Forms")
    )
    service_periods = models.ManyToManyField(
        ServicePeriodValue,
        through='MaintenanceSchedule',
        blank=True,
        help_text=_("Service periods applicable for this product"),
        verbose_name=_("Service Periods")
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Item Master")
        verbose_name_plural = _("Item Masters")

class InventoryItem(models.Model):
    name = models.ForeignKey(ItemMaster, on_delete=models.CASCADE, related_name='inventory_items', verbose_name=_("Item Master"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Quantity"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Created By"))
    production_date = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name=_("Production Date"))
    serial_no = models.CharField(max_length=100, blank=True, verbose_name=_("Serial Number"))
    in_used = models.BooleanField(default=False, verbose_name=_("In Use"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    qr_code_image = models.ImageField(upload_to=get_qrcode_upload_path, null=True, blank=True, verbose_name=_("QR Code Image"))

    def __str__(self):
        shortcode = self.name.shortcode if self.name.shortcode else "NO-CODE"
        serial = self.serial_no if self.serial_no else f"INV-{self.pk}"
        return f"{shortcode} - {serial}"

    class Meta:
        verbose_name = _("Inventory Item")
        verbose_name_plural = _("Inventory Items")

    def generate_qr_code(self):
        """Generate a QR code and save it to the qr_code_image field"""
        if not self.serial_no:
            self.serial_no = f"INV-{self.pk or 'TEMP'}"
        
        # Create QR code data (you can customize this JSON structure)
        qr_data = {
            'id': self.id,
            'code': self.serial_no,
            'name': self.name.name,
            'serial': self.serial_no,
            'production_date': self.production_date.isoformat() if self.production_date else None
        }
        
        # Convert to string for QR code
        qr_string = f"ID:{self.id}|CODE:{self.serial_no}|NAME:{self.name.name}|SERIAL:{self.serial_no}"
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)

        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Save to model field
        filename = f"{self.serial_no}_qr.png"
        self.qr_code_image.save(
            filename,
            File(qr_buffer),
            save=False
        )
        # filename = f"{self.serial_no}_qr.png"
        # self.qr_code_image.save(
        #     filename,
        #     File(qr_buffer),
        #     save=False
        # )
    
    def save(self, *args, **kwargs):
        if not self.serial_no:
            self.serial_no = f"INV-{self.pk or 'TEMP'}"
        
        # Save first to get an ID
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Generate QR code after saving (so we have an ID)
        if is_new or not self.qr_code_image:
            self.generate_qr_code()
            super().save(update_fields=['qr_code_image'])

class InventoryItemAttribute(models.Model):
    """Stores multiple attribute entries for an inventory item"""
    inventory_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='attributes',
        verbose_name=_("Inventory Item")
    )
    attribute_type = models.ForeignKey(
        AttributeType,
        on_delete=models.CASCADE,
        verbose_name=_('Attribute Type'),
        null=True,
        blank=True,
    )
    value = models.CharField(max_length=255, null=True, verbose_name=_("Value"))
    unit = models.ForeignKey(AttributeUnit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Unit"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _('Inventory Item Attribute')
        verbose_name_plural = _('Inventory Item Attributes')
        ordering = ['attribute_type__name']
        # Ensure unique combination of inventory_item, attribute_type and unit
        # This allows same attribute type with different units (e.g., length in both cm and inch)
        unique_together = ('inventory_item', 'attribute_type', 'unit')

    def clean(self):
        """Validate that the unit is compatible with the selected attribute type"""
        from django.core.exceptions import ValidationError
        
        # Check if attribute_type is required
        if not self.attribute_type:
            raise ValidationError({
                'attribute_type': 'ZORUNLU ALAN: Özellik türü seçimi gereklidir. Lütfen listeden bir özellik türü seçin.'
            })
        
        # Check if value is provided
        if not self.value or not self.value.strip():
            raise ValidationError({
                'value': f'ZORUNLU ALAN: "{self.attribute_type.name}" özelliği için değer girişi zorunludur. '
                        f'Lütfen bu özellik için uygun bir değer girin (örn: sayı, metin, ölçüm).'
            })
        
        # Check for duplicate combination of inventory_item, attribute_type and unit
        if self.inventory_item and self.attribute_type:
            existing = InventoryItemAttribute.objects.filter(
                inventory_item=self.inventory_item,
                attribute_type=self.attribute_type,
                unit=self.unit
            )
            
            # If updating, exclude the current instance
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            
            if existing.exists():
                existing_attr = existing.first()
                inventory_name = self.inventory_item.name.name if self.inventory_item.name else "Bu envanter ürünü"
                serial_info = f" (S/N: {self.inventory_item.serial_no})" if self.inventory_item.serial_no else ""
                unit_info = f" ({self.unit.name})" if self.unit else " (birimi belirtilmemiş)"
                
                raise ValidationError({
                    'unit': f'ÇAKIŞMA HATASI: {inventory_name}{serial_info} için "{self.attribute_type.name}" özelliği{unit_info} zaten mevcut! '
                           f'Mevcut kayıt: "{existing_attr.value}"{unit_info} (Oluşturma: {existing_attr.created_at.strftime("%d.%m.%Y %H:%M")}). '
                           f'Aynı özellik türü ve birim kombinasyonu tekrar kaydedilemez. '
                           f'Seçenekleriniz: 1) Farklı bir birim seçin, 2) Mevcut kaydı güncelleyin, 3) Mevcut kaydı silin.'
                })
        
        if self.unit and self.attribute_type:
            # Check if there's a relationship between the attribute type and unit
            if not AttributeTypeUnit.objects.filter(
                attribute_type=self.attribute_type,
                attribute_unit=self.unit
            ).exists():
                # Get available units for this attribute type
                available_units = AttributeUnit.objects.filter(
                    unit_types__attribute_type=self.attribute_type
                ).values_list('name', flat=True)
                
                raise ValidationError({
                    'unit': f'BİRİM UYUMSUZLUĞU: "{self.unit.name}" birimi "{self.attribute_type.name}" özellik türü ile uyumlu değil! '
                           f'Bu özellik türü için sistemde tanımlı birimler: '
                           f'{", ".join(available_units) if available_units else "Henüz hiç birim tanımlanmamış"}. '
                           f'Çözüm: Uyumlu birimlerden birini seçin veya sistem yöneticisinden "{self.unit.name}" biriminin '
                           f'"{self.attribute_type.name}" özelliği için tanımlanmasını isteyin.'
                })
        
        # Check if attribute type requires a unit but no unit is selected
        if self.attribute_type:
            available_units = AttributeUnit.objects.filter(
                unit_types__attribute_type=self.attribute_type
            )
            if available_units.exists() and not self.unit:
                default_unit = available_units.filter(unit_types__is_default=True).first()
                unit_names = available_units.values_list('name', flat=True)
                
                raise ValidationError({
                    'unit': f'BİRİM SEÇİMİ GEREKLİ: "{self.attribute_type.name}" özelliği için birim seçimi zorunludur! '
                           f'Bu özellik türü için kullanılabilir birimler: {", ".join(unit_names)}. '
                           f'{"🎯 Önerilen birim: " + default_unit.name if default_unit else "Varsayılan birim tanımlanmamış."} '
                           f'Lütfen uygun bir birim seçerek tekrar deneyin.'
                })

    def save(self, *args, **kwargs):
        # Always run validation before saving
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        unit_display = f" {self.unit.symbol}" if self.unit else ""
        attr_name = self.attribute_type.name if self.attribute_type else "Unknown"
        return f"{attr_name}: {self.value}{unit_display}"

    def get_available_units(self):
        """Get available units for the current attribute type"""
        if self.attribute_type:
            return AttributeUnit.objects.filter(
                unit_types__attribute_type=self.attribute_type
            ).order_by('unit_types__is_default', 'name')
        return AttributeUnit.objects.none()