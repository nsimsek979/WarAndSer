from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
import os

User = get_user_model()


def installation_image_upload_path(instance, filename):
    """Generate upload path for installation images"""
    customer_name = instance.installation.customer.name.replace(' ', '_').replace('/', '_')
    installation_id = instance.installation.id
    # Count existing images for this installation
    existing_count = instance.installation.images.count() + 1
    
    # Get file extension
    _, ext = os.path.splitext(filename)
    
    # Generate new filename: customername-installation-1.jpg
    new_filename = f"{customer_name}-installation-{existing_count}{ext}"
    
    return f'installations/{installation_id}/images/{new_filename}'


def installation_document_upload_path(instance, filename):
    """Generate upload path for installation documents"""
    customer_name = instance.installation.customer.name.replace(' ', '_').replace('/', '_')
    installation_id = instance.installation.id
    # Count existing documents for this installation
    existing_count = instance.installation.documents.count() + 1
    
    # Get file extension
    _, ext = os.path.splitext(filename)
    
    # Generate new filename: customername-installation-doc-1.pdf
    new_filename = f"{customer_name}-installation-doc-{existing_count}{ext}"
    
    return f'installations/{installation_id}/documents/{new_filename}'


class Installation(models.Model):
    """
    Model for tracking equipment installations at customer locations.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=_("Installer User"),
        help_text=_("User who performed the installation")
    )
    setup_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Setup Date"),
        help_text=_("Date and time when the installation was completed")
    )
    inventory_item = models.ForeignKey(
        'item_master.InventoryItem',
        on_delete=models.PROTECT,
        verbose_name=_("Inventory Item"),
        help_text=_("Inventory item to be installed")
    )
    customer = models.ForeignKey(
        'customer.Company',
        on_delete=models.PROTECT,
        limit_choices_to={'company_type': 'enduser'},
        verbose_name=_("Customer"),
        help_text=_("End user customer where equipment is installed")
    )
    location_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        verbose_name=_("Latitude"),
        help_text=_("GPS latitude coordinate")
    )
    location_longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        verbose_name=_("Longitude"),
        help_text=_("GPS longitude coordinate")
    )
    location_address = models.TextField(
        blank=True,
        verbose_name=_("Installation Address"),
        help_text=_("Detailed address of installation location")
    )
    installation_notes = models.TextField(
        blank=True,
        verbose_name=_("Installation Notes"),
        help_text=_("Additional notes about the installation")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Installation")
        verbose_name_plural = _("Installations")
        ordering = ['-setup_date']

    def __str__(self):
        return f"{self.inventory_item} - {self.customer.name} ({self.setup_date.strftime('%d.%m.%Y')})"

    def save(self, *args, **kwargs):
        """Mark inventory item as in use when installation is saved"""
        # Handle inventory item changes for existing installations
        old_inventory_item = None
        is_new_installation = not self.pk
        
        if self.pk:
            try:
                old_installation = Installation.objects.get(pk=self.pk)
                old_inventory_item = old_installation.inventory_item
            except Installation.DoesNotExist:
                is_new_installation = True
        
        # First save the installation
        super().save(*args, **kwargs)
        
        # Mark new inventory item as in use
        if self.inventory_item and not self.inventory_item.in_used:
            self.inventory_item.in_used = True
            self.inventory_item.save()
        
        # Free up old inventory item if changed
        if old_inventory_item and old_inventory_item != self.inventory_item:
            old_inventory_item.in_used = False
            old_inventory_item.save()
        
        # Create warranty follow-ups for new installations
        if is_new_installation:
            self.create_warranty_and_service_followups()

    def clean(self):
        """Validate installation data"""
        if self.inventory_item:
            # Check if inventory item is available (skip check for existing installations with same item)
            if self.inventory_item.in_used:
                # If this is an existing installation being updated
                if self.pk:
                    try:
                        existing_installation = Installation.objects.get(pk=self.pk)
                        # Allow if it's the same inventory item
                        if existing_installation.inventory_item != self.inventory_item:
                            raise ValidationError({
                                'inventory_item': _('Selected inventory item is already in use.')
                            })
                    except Installation.DoesNotExist:
                        # New installation with used item - not allowed
                        raise ValidationError({
                            'inventory_item': _('Selected inventory item is already in use.')
                        })
                else:
                    # New installation with used item - not allowed
                    raise ValidationError({
                        'inventory_item': _('Selected inventory item is already in use.')
                    })
        
        if self.customer and self.customer.company_type != 'enduser':
            raise ValidationError({
                'customer': _('Installations can only be made for end user customers.')
            })

    @property
    def has_location(self):
        """Check if installation has GPS coordinates"""
        return self.location_latitude is not None and self.location_longitude is not None

    @property
    def location_display(self):
        """Get formatted location display"""
        if self.has_location:
            return f"{self.location_latitude}, {self.location_longitude}"
        return _("Location not set")

    def create_warranty_and_service_followups(self):
        """
        Create warranty and service follow-ups for this installation.
        Called automatically when installation is created.
        """
        # Create warranty follow-ups based on item master warranty values
        WarrantyFollowUp.create_warranty_followups(self)
        
        # Create default service follow-ups
        default_services = [
            {'type': 'time_term', 'value': 6, 'note': 'Default 6 month service interval'},
            {'type': 'working_hours', 'value': 1000, 'note': 'Default 1000 hours service interval'},
        ]
        
        for service_config in default_services:
            ServiceFollowUp.objects.get_or_create(
                installation=self,
                service_type=service_config['type'],
                service_value=service_config['value'],
                defaults={
                    'calculation_notes': service_config['note']
                }
            )


class InstallationImage(models.Model):
    """
    Model for storing installation images (photos taken during installation).
    """
    installation = models.ForeignKey(
        Installation,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_("Installation")
    )
    image = models.ImageField(
        upload_to=installation_image_upload_path,
        verbose_name=_("Installation Image"),
        help_text=_("Photo taken during installation")
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Image Title"),
        help_text=_("Descriptive title for the image")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Image Description"),
        help_text=_("Detailed description of what the image shows")
    )
    image_type = models.CharField(
        max_length=50,
        choices=[
            ('before', _('Before Installation')),
            ('during', _('During Installation')),
            ('after', _('After Installation')),
            ('equipment', _('Equipment Photo')),
            ('location', _('Location Photo')),
            ('documentation', _('Documentation Photo')),
            ('other', _('Other')),
        ],
        default='during',
        verbose_name=_("Image Type")
    )
    captured_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Captured At"),
        help_text=_("When the photo was taken")
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Uploaded By"),
        help_text=_("User who uploaded the image")
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("File Size (bytes)")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Installation Image")
        verbose_name_plural = _("Installation Images")
        ordering = ['-captured_at']

    def __str__(self):
        title = self.title or f"Image {self.id}"
        return f"{self.installation} - {title} ({self.get_image_type_display()})"

    def create_warranty_and_service_followups(self):
        """
        Create warranty and service follow-ups for this installation.
        Called automatically when installation is created.
        """
        # Import here to avoid circular import
        from .models import WarrantyFollowUp, ServiceFollowUp
        
        # Create warranty follow-ups based on item master warranty values
        item_master = self.inventory_item.name  # name is the ItemMaster FK
        
        # Check if item has warranty values
        if hasattr(item_master, 'warranties') and item_master.warranties.exists():
            for warranty_value in item_master.warranties.all():
                # Determine warranty type based on warranty value type
                if hasattr(warranty_value, 'warranty_type'):
                    warranty_type = 'time_term' if 'year' in warranty_value.warranty_type.name.lower() else 'working_hours'
                else:
                    warranty_type = 'time_term'  # Default
                
                WarrantyFollowUp.objects.get_or_create(
                    installation=self,
                    warranty_type=warranty_type,
                    warranty_value=warranty_value.value,
                    defaults={
                        'calculation_notes': f"Auto-created from item warranty: {warranty_value}"
                    }
                )
        else:
            # Create default warranty follow-ups if no specific warranties defined
            default_warranties = [
                {'type': 'time_term', 'value': 1, 'note': 'Default 1 year warranty'},
                {'type': 'working_hours', 'value': 2000, 'note': 'Default 2000 hours warranty'},
            ]
            
            for warranty_config in default_warranties:
                WarrantyFollowUp.objects.get_or_create(
                    installation=self,
                    warranty_type=warranty_config['type'],
                    warranty_value=warranty_config['value'],
                    defaults={
                        'calculation_notes': warranty_config['note']
                    }
                )
        
        # Create default service follow-ups
        default_services = [
            {'type': 'time_term', 'value': 6, 'note': 'Default 6 month service interval'},
            {'type': 'working_hours', 'value': 1000, 'note': 'Default 1000 hours service interval'},
        ]
        
        for service_config in default_services:
            ServiceFollowUp.objects.get_or_create(
                installation=self,
                service_type=service_config['type'],
                service_value=service_config['value'],
                defaults={
                    'calculation_notes': service_config['note']
                }
            )

    def save(self, *args, **kwargs):
        # Auto-generate title if not provided
        if not self.title and self.image:
            customer_name = self.installation.customer.name
            existing_count = self.installation.images.count() + 1
            self.title = f"{customer_name} - Installation Image {existing_count}"
        
        # Set file size
        if self.image and hasattr(self.image, 'size'):
            self.file_size = self.image.size
            
        super().save(*args, **kwargs)

    @property
    def file_size_display(self):
        """Human readable file size"""
        if self.file_size:
            if self.file_size < 1024:
                return f"{self.file_size} B"
            elif self.file_size < 1024 * 1024:
                return f"{self.file_size / 1024:.1f} KB"
            else:
                return f"{self.file_size / (1024 * 1024):.1f} MB"
        return "Unknown size"


class InstallationDocument(models.Model):
    """
    Model for storing installation documents (manuals, certificates, reports, etc.).
    """
    installation = models.ForeignKey(
        Installation,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_("Installation")
    )
    document = models.FileField(
        upload_to=installation_document_upload_path,
        verbose_name=_("Installation Document"),
        help_text=_("Document related to the installation")
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_("Document Title"),
        help_text=_("Descriptive title for the document")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Document Description"),
        help_text=_("Detailed description of the document content")
    )
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('manual', _('Installation Manual')),
            ('certificate', _('Installation Certificate')),
            ('report', _('Installation Report')),
            ('checklist', _('Installation Checklist')),
            ('warranty', _('Warranty Document')),
            ('specification', _('Technical Specification')),
            ('contract', _('Installation Contract')),
            ('invoice', _('Invoice/Receipt')),
            ('other', _('Other Document')),
        ],
        default='report',
        verbose_name=_("Document Type")
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Uploaded At")
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Uploaded By"),
        help_text=_("User who uploaded the document")
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("File Size (bytes)")
    )
    file_extension = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("File Extension")
    )
    is_required = models.BooleanField(
        default=False,
        verbose_name=_("Required Document"),
        help_text=_("Mark as required document for this installation")
    )
    is_confidential = models.BooleanField(
        default=False,
        verbose_name=_("Confidential"),
        help_text=_("Mark as confidential document (restricted access)")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Installation Document")
        verbose_name_plural = _("Installation Documents")
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.installation} - {self.title} ({self.get_document_type_display()})"

    def save(self, *args, **kwargs):
        # Auto-generate title if not provided
        if not self.title and self.document:
            customer_name = self.installation.customer.name
            existing_count = self.installation.documents.count() + 1
            self.title = f"{customer_name} - Installation Document {existing_count}"
        
        if self.document:
            # Set file size
            if hasattr(self.document, 'size'):
                self.file_size = self.document.size
            
            # Set file extension
            if hasattr(self.document, 'name'):
                self.file_extension = os.path.splitext(self.document.name)[1].lower()
        
        super().save(*args, **kwargs)

    @property
    def file_size_display(self):
        """Human readable file size"""
        if self.file_size:
            if self.file_size < 1024:
                return f"{self.file_size} B"
            elif self.file_size < 1024 * 1024:
                return f"{self.file_size / 1024:.1f} KB"
            else:
                return f"{self.file_size / (1024 * 1024):.1f} MB"
        return "Unknown size"

    @property
    def is_image(self):
        """Check if document is an image file"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        return self.file_extension.lower() in image_extensions

    @property
    def is_pdf(self):
        """Check if document is a PDF file"""
        return self.file_extension.lower() == '.pdf'

    def clean(self):
        """Validate document upload"""
        if self.document:
            # Check file size (max 50MB)
            max_size = 50 * 1024 * 1024  # 50MB
            if hasattr(self.document, 'size') and self.document.size > max_size:
                raise ValidationError({
                    'document': _('File size cannot exceed 50MB.')
                })
            
            # Check file extension
            allowed_extensions = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.txt', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'
            ]
            if hasattr(self.document, 'name'):
                ext = os.path.splitext(self.document.name)[1].lower()
                if ext not in allowed_extensions:
                    raise ValidationError({
                        'document': _('File type not allowed. Allowed types: PDF, DOC, XLS, PPT, TXT, Images.')
                    })


class WarrantyFollowUp(models.Model):
    """
    Model for tracking warranty end dates based on different warranty types.
    Supports both time-based and working hours-based warranty calculations.
    """
    WARRANTY_TYPE_CHOICES = [
        ('time_term', _('Time-Term Warranty (Year Based)')),
        ('working_hours', _('Working Hours Warranty')),
    ]

    installation = models.ForeignKey(
        Installation,
        on_delete=models.CASCADE,
        related_name='warranty_followups',
        verbose_name=_("Installation")
    )
    warranty_type = models.CharField(
        max_length=20,
        choices=WARRANTY_TYPE_CHOICES,
        verbose_name=_("Warranty Type")
    )
    warranty_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Warranty Value"),
        help_text=_("Years for time-term warranty, Hours for working hours warranty")
    )
    end_of_warranty_date = models.DateTimeField(
        verbose_name=_("End of Warranty Date"),
        help_text=_("Calculated warranty end date")
    )
    calculation_notes = models.TextField(
        blank=True,
        verbose_name=_("Calculation Notes"),
        help_text=_("Details about how the warranty end date was calculated")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Warranty Follow-Up")
        verbose_name_plural = _("Warranty Follow-Ups")
        ordering = ['end_of_warranty_date']
        unique_together = ['installation', 'warranty_type', 'warranty_value']

    def __str__(self):
        return f"{self.installation} - {self.get_warranty_type_display()} ({self.end_of_warranty_date.strftime('%d.%m.%Y')})"

    def save(self, *args, **kwargs):
        """Calculate warranty end date before saving"""
        if not self.end_of_warranty_date:
            self.end_of_warranty_date = self.calculate_warranty_end_date()
        super().save(*args, **kwargs)

    def calculate_warranty_end_date(self):
        """
        Calculate warranty end date based on warranty type and customer working hours.
        """
        setup_date = self.installation.setup_date
        
        if self.warranty_type == 'time_term':
            # Time-based warranty: setup_date + years
            years = int(self.warranty_value)
            end_date = setup_date + timedelta(days=years * 365)
            self.calculation_notes = f"Time-term warranty: {years} year(s) from setup date"
            
        elif self.warranty_type == 'working_hours':
            # Working hours-based warranty
            warranty_hours = float(self.warranty_value)
            
            try:
                working_hours = self.installation.customer.working_hours
                weekly_hours = working_hours.weekly_working_hours
                
                if weekly_hours > 0:
                    # Calculate weeks needed to reach warranty hours
                    weeks_needed = warranty_hours / weekly_hours
                    days_needed = weeks_needed * 7
                    
                    end_date = setup_date + timedelta(days=days_needed)
                    
                    self.calculation_notes = (
                        f"Working hours warranty: {warranty_hours} hours, "
                        f"Weekly working hours: {weekly_hours}, "
                        f"Calculated duration: {weeks_needed:.1f} weeks ({days_needed:.0f} days)"
                    )
                else:
                    # Fallback if no working hours defined
                    # Assume 8 hours/day, 5 days/week = 40 hours/week
                    weeks_needed = warranty_hours / 40
                    days_needed = weeks_needed * 7
                    end_date = setup_date + timedelta(days=days_needed)
                    
                    self.calculation_notes = (
                        f"Working hours warranty: {warranty_hours} hours, "
                        f"Default 40 hours/week used (no working hours configured), "
                        f"Calculated duration: {weeks_needed:.1f} weeks ({days_needed:.0f} days)"
                    )
                    
            except AttributeError:
                # Customer has no working hours configured
                # Fallback to default calculation
                weeks_needed = warranty_hours / 40  # 40 hours per week default
                days_needed = weeks_needed * 7
                end_date = setup_date + timedelta(days=days_needed)
                
                self.calculation_notes = (
                    f"Working hours warranty: {warranty_hours} hours, "
                    f"Default 40 hours/week used (customer has no working hours configured), "
                    f"Calculated duration: {weeks_needed:.1f} weeks ({days_needed:.0f} days)"
                )
        
        else:
            # Default fallback
            end_date = setup_date + timedelta(days=365)
            self.calculation_notes = "Default 1 year warranty applied"
        
        return end_date

    @property
    def is_active(self):
        """Check if warranty is still active"""
        return datetime.now() <= self.end_of_warranty_date.replace(tzinfo=None)

    @property
    def days_remaining(self):
        """Get remaining warranty days"""
        if self.is_active:
            delta = self.end_of_warranty_date.replace(tzinfo=None) - datetime.now()
            return delta.days
        return 0

    @classmethod
    def create_warranty_followups(cls, installation):
        """
        Create warranty follow-ups based on item master warranty values.
        Bu method bir ürün için birden fazla garanti süresi (hem yıl bazlı hem çalışma saati) 
        kayıt edilmesini destekler.
        """
        item_master = installation.inventory_item.name  # name is the ItemMaster FK
        
        # Get all warranty values for this item
        warranty_values = item_master.warranties.all()
        created_warranties = []
        
        if warranty_values.exists():
            print(f"ItemMaster '{item_master.name}' için {warranty_values.count()} garanti süresi bulundu:")
            
            for warranty_value in warranty_values:
                # Determine warranty type based on warranty type name
                warranty_type_name = warranty_value.warranty_type.type.lower()
                
                # Map warranty type names to warranty follow-up types
                if 'yıl' in warranty_type_name or 'year' in warranty_type_name:
                    warranty_type = 'time_term'
                    type_description = "Yıl bazlı garanti"
                elif 'hour' in warranty_type_name or 'saat' in warranty_type_name:
                    warranty_type = 'working_hours'
                    type_description = "Çalışma saati bazlı garanti"
                else:
                    # Default to time_term if type is unclear
                    warranty_type = 'time_term'
                    type_description = "Varsayılan yıl bazlı garanti"
                
                print(f"  - {warranty_value.warranty_type.type}: {warranty_value.value} ({type_description})")
                
                # Create warranty follow-up for each warranty type/value
                warranty_followup, created = cls.objects.get_or_create(
                    installation=installation,
                    warranty_type=warranty_type,
                    warranty_value=warranty_value.value,
                    defaults={
                        'calculation_notes': f"Otomatik oluşturuldu - {warranty_value.warranty_type.type} ({type_description})"
                    }
                )
                
                if created:
                    created_warranties.append(warranty_followup)
                    print(f"    ✓ Garanti takibi oluşturuldu: {warranty_followup}")
                else:
                    print(f"    → Garanti takibi zaten mevcut: {warranty_followup}")
        else:
            print(f"ItemMaster '{item_master.name}' için garanti süresi tanımlı değil, varsayılan garantiler oluşturuluyor:")
            
            # Create default warranty follow-ups if no specific warranties defined
            default_warranties = [
                {'type': 'time_term', 'value': 1, 'note': 'Varsayılan 1 yıl garanti (ürün için garanti tanımlı değil)', 'desc': 'Yıl bazlı'},
                {'type': 'working_hours', 'value': 2000, 'note': 'Varsayılan 2000 saat garanti (ürün için garanti tanımlı değil)', 'desc': 'Çalışma saati bazlı'},
            ]
            
            for warranty_config in default_warranties:
                print(f"  - Varsayılan {warranty_config['desc']}: {warranty_config['value']}")
                
                warranty_followup, created = cls.objects.get_or_create(
                    installation=installation,
                    warranty_type=warranty_config['type'],
                    warranty_value=warranty_config['value'],
                    defaults={
                        'calculation_notes': warranty_config['note']
                    }
                )
                
                if created:
                    created_warranties.append(warranty_followup)
                    print(f"    ✓ Varsayılan garanti takibi oluşturuldu: {warranty_followup}")
                else:
                    print(f"    → Varsayılan garanti takibi zaten mevcut: {warranty_followup}")
        
        print(f"Toplam {len(created_warranties)} yeni garanti takibi oluşturuldu.")
        return created_warranties


class ServiceFollowUp(models.Model):
    """
    Model for tracking service schedules based on different service types.
    Similar to warranty but for maintenance/service intervals.
    """
    SERVICE_TYPE_CHOICES = [
        ('time_term', _('Time-Term Service (Month Based)')),
        ('working_hours', _('Working Hours Service')),
    ]

    installation = models.ForeignKey(
        Installation,
        on_delete=models.CASCADE,
        related_name='service_followups',
        verbose_name=_("Installation")
    )
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPE_CHOICES,
        verbose_name=_("Service Type")
    )
    service_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Service Value"),
        help_text=_("Months for time-term service, Hours for working hours service")
    )
    next_service_date = models.DateTimeField(
        verbose_name=_("Next Service Date"),
        help_text=_("Calculated next service date")
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name=_("Service Completed"),
        help_text=_("Mark as completed when service is done")
    )
    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Completion Date")
    )
    calculation_notes = models.TextField(
        blank=True,
        verbose_name=_("Calculation Notes"),
        help_text=_("Details about how the service date was calculated")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Service Follow-Up")
        verbose_name_plural = _("Service Follow-Ups")
        ordering = ['next_service_date']

    def __str__(self):
        status = "✓" if self.is_completed else "⏳"
        return f"{status} {self.installation} - {self.get_service_type_display()} ({self.next_service_date.strftime('%d.%m.%Y')})"

    def save(self, *args, **kwargs):
        """Calculate service date before saving"""
        if not self.next_service_date:
            self.next_service_date = self.calculate_next_service_date()
        super().save(*args, **kwargs)

    def calculate_next_service_date(self):
        """
        Calculate next service date based on service type and customer working hours.
        """
        setup_date = self.installation.setup_date
        
        if self.service_type == 'time_term':
            # Time-based service: setup_date + months
            months = int(self.service_value)
            end_date = setup_date + timedelta(days=months * 30)  # Approximate month calculation
            self.calculation_notes = f"Time-term service: {months} month(s) from setup date"
            
        elif self.service_type == 'working_hours':
            # Working hours-based service
            service_hours = float(self.service_value)
            
            try:
                working_hours = self.installation.customer.working_hours
                weekly_hours = working_hours.weekly_working_hours
                
                if weekly_hours > 0:
                    weeks_needed = service_hours / weekly_hours
                    days_needed = weeks_needed * 7
                    end_date = setup_date + timedelta(days=days_needed)
                    
                    self.calculation_notes = (
                        f"Working hours service: {service_hours} hours, "
                        f"Weekly working hours: {weekly_hours}, "
                        f"Calculated duration: {weeks_needed:.1f} weeks ({days_needed:.0f} days)"
                    )
                else:
                    # Fallback
                    weeks_needed = service_hours / 40
                    days_needed = weeks_needed * 7
                    end_date = setup_date + timedelta(days=days_needed)
                    
                    self.calculation_notes = (
                        f"Working hours service: {service_hours} hours, "
                        f"Default 40 hours/week used, "
                        f"Calculated duration: {weeks_needed:.1f} weeks ({days_needed:.0f} days)"
                    )
                    
            except AttributeError:
                # Customer has no working hours configured
                weeks_needed = service_hours / 40
                days_needed = weeks_needed * 7
                end_date = setup_date + timedelta(days=days_needed)
                
                self.calculation_notes = (
                    f"Working hours service: {service_hours} hours, "
                    f"Default 40 hours/week used (no working hours configured), "
                    f"Calculated duration: {weeks_needed:.1f} weeks ({days_needed:.0f} days)"
                )
        
        else:
            # Default fallback
            end_date = setup_date + timedelta(days=90)  # 3 months default
            self.calculation_notes = "Default 3 month service interval applied"
        
        return end_date

    @property
    def is_due(self):
        """Check if service is due"""
        return datetime.now() >= self.next_service_date.replace(tzinfo=None) and not self.is_completed

    @property
    def days_until_due(self):
        """Get days until service is due"""
        if not self.is_completed:
            delta = self.next_service_date.replace(tzinfo=None) - datetime.now()
            return delta.days
        return None

    def mark_completed(self):
        """Mark service as completed"""
        self.is_completed = True
        self.completed_date = datetime.now()
        self.save()

    @classmethod
    def create_service_followups(cls, installation):
        """
        Create service follow-ups based on item master service values.
        This method should be called after installation is saved.
        """
        item_master = installation.inventory_item.name  # name is the ItemMaster FK
        
        # Get all service values for this item (assuming similar structure to warranty)
        # You may need to adjust this based on your actual item_master service configuration
        # service_values = item_master.servicevalue_set.all()
        
        # For now, create default service intervals
        # This can be enhanced later when service configuration is added to item_master
        default_services = [
            {'type': 'time_term', 'value': 6},  # 6 months
            {'type': 'working_hours', 'value': 1000},  # 1000 hours
        ]
        
        for service_config in default_services:
            cls.objects.get_or_create(
                installation=installation,
                service_type=service_config['type'],
                service_value=service_config['value'],
                defaults={
                    'calculation_notes': f"Default service interval: {service_config['value']} {service_config['type']}"
                }
            )
