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
    symbol = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Attribute Unit'
        verbose_name_plural = 'Attribute Units'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.symbol})"

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
        return f"{self.name.name} - {self.item_code}"

    def generate_qr_code(self):
        """Generate a QR code and save it to the qr_code_image field"""
        if not self.item_code:
            self.item_code = f"INV-{self.pk or 'TEMP'}"
        
        # Create QR code data (you can customize this JSON structure)
        qr_data = {
            'id': self.id,
            'code': self.item_code,
            'name': self.name.name,
            'serial': self.serial_no,
            'production_date': self.production_date.isoformat() if self.production_date else None
        }
        
        # Convert to string for QR code
        qr_string = f"ID:{self.id}|CODE:{self.item_code}|NAME:{self.name.name}|SERIAL:{self.serial_no}"
        
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
        filename = f"{self.item_code}_qr.png"
        self.qr_code_image.save(
            filename,
            File(qr_buffer),
            save=False
        )
    
    def save(self, *args, **kwargs):
        if not self.item_code:
            self.item_code = f"INV-{self.pk or 'TEMP'}"
        
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
        unique_together = ('inventory_item', 'attribute_type', 'unit', 'value')

    def __str__(self):
        unit_display = f" {self.unit.symbol}" if self.unit else ""
        return f"{self.attribute_type}: {self.value}{unit_display}"