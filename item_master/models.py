from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.conf import settings
import qrcode
from PIL import Image
import os
from io import BytesIO
from django.core.files import File

User = get_user_model()

def get_qrcode_upload_path(instance, filename):
    """Generate upload path for QR code images"""
    return f'qrcodes/{instance.id}/{filename}'

class Status(models.Model):
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.status

class StockType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='brands/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, default=None)
    slug = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.category_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.category_name

class ItemImage(models.Model):
    item = models.ForeignKey('ItemMaster', on_delete=models.CASCADE, related_name='images')
    url = models.ImageField(upload_to='item_images/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item.name} - {self.id}"

class ItemSpec(models.Model):
    item = models.ForeignKey('ItemMaster', on_delete=models.CASCADE, related_name='specs')
    url = models.FileField(upload_to='item_specs/', unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item.name} - {self.id}"

class WarrantyType(models.Model):
    type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.type

class WarrantyValue(models.Model):
    warranty_type = models.ForeignKey(WarrantyType, on_delete=models.CASCADE)
    value = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.warranty_type}: {self.value}"

class ServicePeriodType(models.Model):
    """Servis periyodu türleri (Ay bazlı, Çalışma saati bazlı, vb.)"""
    type = models.CharField(max_length=100, help_text="Örn: Ay bazlı, Çalışma saati bazlı, Kilometre bazlı")
    unit = models.CharField(max_length=50, help_text="Örn: ay, saat, km")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Servis Periyodu Türü'
        verbose_name_plural = 'Servis Periyodu Türleri'

    def __str__(self):
        return f"{self.type} ({self.unit})"

class ServicePeriodValue(models.Model):
    """Servis periyodu değerleri"""
    service_period_type = models.ForeignKey(ServicePeriodType, on_delete=models.CASCADE)
    value = models.FloatField(help_text="Örn: 6 ay, 3000 saat, 10000 km")
    description = models.CharField(max_length=200, blank=True, help_text="Opsiyonel açıklama")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Servis Periyodu Değeri'
        verbose_name_plural = 'Servis Periyodu Değerleri'

    def __str__(self):
        return f"{self.value} {self.service_period_type.unit} - {self.service_period_type.type}"

class MaintenanceSchedule(models.Model):
    """Ana bakım programı - hangi ürün için hangi servis periyotları geçerli"""
    item_master = models.ForeignKey('ItemMaster', on_delete=models.CASCADE, related_name='maintenance_schedules')
    service_period_value = models.ForeignKey(ServicePeriodValue, on_delete=models.CASCADE)
    is_critical = models.BooleanField(default=True, help_text="Kritik bakım mı?")
    maintenance_description = models.TextField(blank=True, help_text="Bakım açıklaması")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bakım Programı'
        verbose_name_plural = 'Bakım Programları'
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
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class AttributeType(models.Model):
    """Types of attributes that can be assigned to inventory items"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Attribute Type'
        verbose_name_plural = 'Attribute Types'
        ordering = ['name']

    def __str__(self):
        return self.name

class AttributeUnit(models.Model):
    """Units of measurement for attributes"""
    name = models.CharField(max_length=50, unique=True)
    symbol = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Attribute Unit'
        verbose_name_plural = 'Attribute Units'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class AttributeTypeUnit(models.Model):
    """Relationship between AttributeType and AttributeUnit"""
    attribute_type = models.ForeignKey(
        AttributeType, 
        on_delete=models.CASCADE, 
        related_name='type_units'
    )
    attribute_unit = models.ForeignKey(
        AttributeUnit, 
        on_delete=models.CASCADE, 
        related_name='unit_types'
    )
    is_default = models.BooleanField(
        default=False, 
        help_text="Is this the default unit for this attribute type?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Attribute Type Unit'
        verbose_name_plural = 'Attribute Type Units'
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
    main_item = models.ForeignKey('ItemMaster', on_delete=models.CASCADE, related_name='main_item_spare_parts_set')
    spare_part_item = models.ForeignKey('ItemMaster', on_delete=models.CASCADE, related_name='spare_part_of_items_set')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('main_item', 'spare_part_item')

    def __str__(self):
        return f"{self.main_item.name} - {self.spare_part_item.name}"

class ItemMaster(models.Model):
    shortcode = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='items')
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True)
    brand_name = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
    stock_type = models.ForeignKey(StockType, on_delete=models.SET_NULL, null=True)
    slug = models.SlugField(max_length=255, unique=True)
    
    spare_parts = models.ManyToManyField(
        "self",
        through='ItemSparePart',
        symmetrical=False,
        blank=True,
        through_fields=('main_item', 'spare_part_item') 
    )
    
    warranties = models.ManyToManyField(
        WarrantyValue, 
        blank=True
    )
    service_forms = models.ManyToManyField(
        ServiceForm, 
        blank=True
    )
    service_periods = models.ManyToManyField(
        ServicePeriodValue,
        through='MaintenanceSchedule',
        blank=True,
        help_text="Bu ürün için geçerli servis periyotları"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class InventoryItem(models.Model):
    name = models.ForeignKey(ItemMaster, on_delete=models.CASCADE, related_name='inventory_items')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    production_date = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    serial_no = models.CharField(max_length=100, blank=True)
    in_used = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    qr_code_image = models.ImageField(upload_to=get_qrcode_upload_path, null=True, blank=True)

    def __str__(self):
        shortcode = self.name.shortcode if self.name.shortcode else "NO-CODE"
        serial = self.serial_no if self.serial_no else f"INV-{self.pk}"
        return f"{shortcode} - {serial}"

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
        related_name='attributes'
    )
    attribute_type = models.ForeignKey(
        AttributeType,
        on_delete=models.CASCADE,
        verbose_name='Type',
        null=True,
        blank=True,
    )
    value = models.CharField(max_length=255, null=True)
    unit = models.ForeignKey(AttributeUnit, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Item Attribute'
        verbose_name_plural = 'Item Attributes'
        ordering = ['attribute_type__name']
        # Removed unique_together to prevent deletion issues

    def clean(self):
        """Validate that the unit is compatible with the selected attribute type"""
        from django.core.exceptions import ValidationError
        
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
                    'unit': f'Unit "{self.unit.name}" is not compatible with attribute type "{self.attribute_type.name}". '
                           f'Available units: {", ".join(available_units) if available_units else "None"}'
                })

    def save(self, *args, **kwargs):
        # Only validate if both attribute_type and unit are set
        if self.attribute_type and self.unit:
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