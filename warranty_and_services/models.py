from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.utils import timezone
import os
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from io import BytesIO

# PDF generation import with fallback
try:
    from weasyprint import HTML
    PDF_AVAILABLE = True
    PDF_ENGINE = 'weasyprint'
except ImportError:
    try:
        from xhtml2pdf import pisa
        PDF_AVAILABLE = True
        PDF_ENGINE = 'xhtml2pdf'
    except ImportError:
        PDF_AVAILABLE = False
        PDF_ENGINE = None

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
    setup_date = models.DateField(
        default=date.today,
        verbose_name=_("Setup Date"),
        help_text=_("Date when the installation was completed")
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
        date_str = self.setup_date.strftime('%d.%m.%Y') if self.setup_date else 'N/A'
        return f"{self.inventory_item} - {self.customer.name} ({date_str})"

    def send_installation_notification(self):
        language = 'tr' if self.customer and self.customer.company_type == 'enduser' and self.customer.name.endswith('A.Ş.') else 'en'
        
        # Collect all warranty and service data for PDF
        warranties = self.warranty_followups.all()
        services = self.service_followups.all()
        images = self.images.all()
        documents = self.documents.all()
        
        # Garanti bitiş ve en yakın servis tarihini bul
        warranty = self.warranty_followups.order_by('end_of_warranty_date').last()
        service = self.service_followups.filter(is_completed=False).order_by('next_service_date').first()
        warranty_end_date = warranty.end_of_warranty_date.strftime('%d.%m.%Y') if warranty else '-'
        next_service_date = service.next_service_date.strftime('%d.%m.%Y') if service else '-'
        
        context = {
            'installation': self,
            'language': language,
            'warranty_end_date': warranty_end_date,
            'next_service_date': next_service_date,
            'warranties': warranties,
            'services': services,
            'images': images,
            'documents': documents,
        }
        subject = 'Kurulum Tamamlandı' if language == 'tr' else 'Installation Completed'
        html_content = render_to_string('warranty_and_services/emails/installation_notification.html', context)
        from_email = settings.DEFAULT_FROM_EMAIL
        # PDF oluştur
        pdf_buffer = BytesIO()
        
        if PDF_ENGINE == 'xhtml2pdf':
            try:
                from xhtml2pdf import pisa
                pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
                pdf_buffer.seek(0)
            except ImportError:
                print("xhtml2pdf not available, skipping PDF generation")
                pdf_buffer = None
        elif PDF_ENGINE == 'weasyprint':
            try:
                from weasyprint import HTML
                HTML(string=html_content).write_pdf(pdf_buffer)
                pdf_buffer.seek(0)
            except ImportError:
                print("weasyprint not available, skipping PDF generation")
                pdf_buffer = None
        else:
            print("No PDF engine available, skipping PDF generation")
            pdf_buffer = None
        # Alıcıları topla
        recipients = set()
        if self.customer and self.customer.email:
            recipients.add(self.customer.email)
        # ContactPerson
        if hasattr(self.customer, 'contactperson_set'):
            for contact in self.customer.contactperson_set.all():
                if contact.email:
                    recipients.add(contact.email)
        # Kurulum yapan kullanıcı
        if self.user and self.user.email:
            recipients.add(self.user.email)
        # Kurulum yapan firmanın manager ve servis personeli
        if self.user.company:
            for u in self.user.company.customuser_set.filter(role__in=[
                'manager_main', 'salesmanager_main', 'service_main',
                'manager_distributor', 'salesmanager_distributor', 'service_distributor']):
                if u.email:
                    recipients.add(u.email)
            # Related manager
            if self.user.company.related_manager and self.user.company.related_manager.email:
                recipients.add(self.user.company.related_manager.email)
        # Mail gönder
        try:
            email = EmailMultiAlternatives(
                subject,
                html_content,
                from_email,
                list(recipients)
            )
            email.attach_alternative(html_content, "text/html")
            
            # PDF attachment - only if PDF was generated successfully
            if pdf_buffer:
                email.attach('installation_details.pdf', pdf_buffer.read(), 'application/pdf')
            
            email.send()
        except Exception as e:
            print(f"Kurulum bildirimi gönderilemedi: {e}")

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
        # Kurulum bildirimi gönder
        self.send_installation_notification()

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
        
        # Create service follow-ups based on item master maintenance schedules
        ServiceFollowUp.create_service_followups(self)


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
    captured_at = models.DateField(
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
                    'calculation_notes': service_config['note'],
                    'completion_notes': ''  # Empty string for new services
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
    uploaded_at = models.DateField(
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
        ('time_term', _('Time-Term Warranty (Month Based)')),
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
    warranty_value = models.PositiveIntegerField(
        verbose_name=_("Warranty Value"),
        help_text=_("Years for time-term warranty, Hours for working hours warranty")
    )
    end_of_warranty_date = models.DateField(
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
        date_str = self.end_of_warranty_date.strftime('%d.%m.%Y') if self.end_of_warranty_date else 'N/A'
        return f"{self.installation} - {self.get_warranty_type_display()} ({date_str})"

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
            # Month-based warranty: setup_date + months * 30 days
            months = int(self.warranty_value)
            end_date = setup_date.date() + timedelta(days=months * 30) if hasattr(setup_date, 'date') else setup_date + timedelta(days=months * 30)
            self.calculation_notes = f"Ay bazlı garanti: {months} ay ({months * 30} gün) kurulum tarihinden itibaren"
            
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
                    
                    end_date = setup_date.date() + timedelta(days=days_needed) if hasattr(setup_date, 'date') else setup_date + timedelta(days=days_needed)
                    
                    self.calculation_notes = (
                        f"Çalışma saati bazlı garanti: {warranty_hours} saat, "
                        f"Haftalık çalışma saati: {weekly_hours}, "
                        f"Hesaplanan süre: {weeks_needed:.1f} hafta ({days_needed:.0f} gün)"
                    )
                else:
                    # Fallback if no working hours defined
                    # Assume 8 hours/day, 5 days/week = 40 hours/week
                    weeks_needed = warranty_hours / 40
                    days_needed = weeks_needed * 7
                    end_date = setup_date.date() + timedelta(days=days_needed) if hasattr(setup_date, 'date') else setup_date + timedelta(days=days_needed)
                    
                    self.calculation_notes = (
                        f"Çalışma saati bazlı garanti: {warranty_hours} saat, "
                        f"Varsayılan 40 saat/hafta kullanıldı (çalışma saati tanımlı değil), "
                        f"Hesaplanan süre: {weeks_needed:.1f} hafta ({days_needed:.0f} gün)"
                    )
                    
            except AttributeError:
                # Customer has no working hours configured
                # Fallback to default calculation
                weeks_needed = warranty_hours / 40  # 40 hours per week default
                days_needed = weeks_needed * 7
                end_date = setup_date.date() + timedelta(days=days_needed) if hasattr(setup_date, 'date') else setup_date + timedelta(days=days_needed)
                
                self.calculation_notes = (
                    f"Çalışma saati bazlı garanti: {warranty_hours} saat, "
                    f"Varsayılan 40 saat/hafta kullanıldı (müşteri çalışma saati yapılandırılmamış), "
                    f"Hesaplanan süre: {weeks_needed:.1f} hafta ({days_needed:.0f} gün)"
                )
        
        else:
            # Default fallback - 6 ay garanti
            end_date = setup_date.date() + timedelta(days=180) if hasattr(setup_date, 'date') else setup_date + timedelta(days=180)
            self.calculation_notes = "Varsayılan 6 ay garanti uygulandı"
        
        return end_date

    @property
    def is_active(self):
        """Check if warranty is still active"""
        return self.end_of_warranty_date and datetime.now().date() <= self.end_of_warranty_date

    @property
    def days_remaining(self):
        """Get remaining warranty days"""
        if self.is_active and self.end_of_warranty_date:
            delta = self.end_of_warranty_date - datetime.now().date()
            return delta.days
        return 0

    @property
    def is_expired(self):
        """Check if warranty has expired"""
        return not self.is_active

    @property
    def is_expiring_soon(self):
        """Check if warranty is expiring within 30 days"""
        if self.is_active and self.end_of_warranty_date:
            days_left = self.days_remaining
            return 0 < days_left <= 30
        return False

    @classmethod
    def create_warranty_followups(cls, installation):
        """
        Create warranty follow-ups based on item master warranty values.
        Bu method bir ürün için birden fazla garanti süresi (hem ay bazlı hem çalışma saati) 
        kayıt edilmesini destekler.
        """
        item_master = installation.inventory_item.name  # name is the ItemMaster FK
        
        # Get all warranty values for this item
        warranty_values = item_master.warranties.all()
        created_warranties = []
        
        if warranty_values.exists():
            print(f"Ana ürün '{item_master.name}' için {warranty_values.count()} garanti süresi bulundu:")
            
            for warranty_value in warranty_values:
                # Use database warranty type name directly
                warranty_type_name = warranty_value.warranty_type.type.lower()
                
                # Map warranty type names to warranty follow-up types
                if 'ay' in warranty_type_name or 'month' in warranty_type_name:
                    warranty_type = 'time_term'
                    type_description = "Ay bazlı garanti"
                elif 'hour' in warranty_type_name or 'saat' in warranty_type_name:
                    warranty_type = 'working_hours'
                    type_description = "Çalışma saati bazlı garanti"
                else:
                    # Default to working_hours if type is unclear
                    warranty_type = 'working_hours'
                    type_description = "Çalışma saati bazlı garanti (varsayılan)"
                
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
            print(f"ItemMaster '{item_master.name}' için garanti süresi tanımlı değil, varsayılan garanti oluşturuluyor:")
            
            # Create default warranty (ay bazlı garanti, 6 ay)
            warranty_followup, created = cls.objects.get_or_create(
                installation=installation,
                warranty_type='time_term',
                warranty_value=6,
                defaults={
                    'calculation_notes': 'Varsayılan 6 ay garanti (ürün için garanti tanımlı değil)'
                }
            )
            
            if created:
                created_warranties.append(warranty_followup)
                print("    ✓ Varsayılan garanti takibi oluşturuldu: 6 ay garanti")
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
    service_value = models.PositiveIntegerField(
        verbose_name=_("Service Value"),
        help_text=_("Months for time-term service, Hours for working hours service")
    )
    next_service_date = models.DateField(
        verbose_name=_("Next Service Date"),
        help_text=_("Calculated next service date")
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name=_("Service Completed"),
        help_text=_("Mark as completed when service is done")
    )
    completed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Completion Date")
    )
    calculation_notes = models.TextField(
        blank=True,
        verbose_name=_("Calculation Notes"),
        help_text=_("Details about how the service date was calculated")
    )
    completion_notes = models.TextField(
        blank=True,
        verbose_name=_("Completion Notes"),
        help_text=_("Notes about the completed service")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Service Follow-Up")
        verbose_name_plural = _("Service Follow-Ups")
        ordering = ['next_service_date']

    def __str__(self):
        status = "✓" if self.is_completed else "⏳"
        date_str = self.next_service_date.strftime('%d.%m.%Y') if self.next_service_date else 'N/A'
        return f"{status} {self.installation} - {self.get_service_type_display()} ({date_str})"

    @property
    def service_status_priority(self):
        """
        Return priority number for service status ordering:
        1 = Overdue (geçmiş)
        2 = Due Soon (yakında)  
        3 = Pending (beklemede)
        4 = Done (tamamlanmış)
        """
        if self.is_completed:
            return 4  # Done
        
        # If no service date set, treat as pending
        if not self.next_service_date:
            return 3  # Pending
        
        today = timezone.now().date()
        # next_service_date is already a DateField, no need to call .date()
        service_date = self.next_service_date
        days_until_service = (service_date - today).days
        
        if days_until_service < 0:
            return 1  # Overdue
        elif days_until_service <= 30:  # Due within 30 days
            return 2  # Due Soon
        else:
            return 3  # Pending

    @property
    def service_status_display(self):
        """Return human-readable service status"""
        priority = self.service_status_priority
        if priority == 1:
            return "Overdue"
        elif priority == 2:
            return "Due Soon"
        elif priority == 3:
            return "Pending"
        else:
            return "Done"

    def save(self, *args, **kwargs):
        """Calculate service date before saving"""
        if not self.next_service_date:
            self.next_service_date = self.calculate_next_service_date()
        super().save(*args, **kwargs)

    def calculate_next_service_date(self, from_date=None):
        """
        Calculate next service date based on service type and customer working hours.
        
        Args:
            from_date: Date to calculate from (default: installation setup date)
        """
        # Use provided date or default to setup date
        base_date = from_date if from_date else self.installation.setup_date
        
        # If no base date available, use today
        if not base_date:
            base_date = date.today()
            
        # Ensure we have a date object and convert datetime to date if needed
        if hasattr(base_date, 'date'):
            # It's a datetime object, extract date
            base_date = base_date.date()
        
        # Now format the date string (base_date should definitely be a date object here)
        base_date_str = base_date.strftime('%d.%m.%Y')
        
        if self.service_type == 'time_term':
            # Time-based service: base_date + months
            months = int(self.service_value)
            end_date = base_date + timedelta(days=months * 30)  # Approximate month calculation
            self.calculation_notes = f"Time-term service: {months} month(s) from {base_date_str}"
            
        elif self.service_type == 'working_hours':
            # Working hours-based service
            service_hours = float(self.service_value)
            
            try:
                working_hours = self.installation.customer.working_hours
                weekly_hours = working_hours.weekly_working_hours
                
                if weekly_hours > 0:
                    weeks_needed = service_hours / weekly_hours
                    days_needed = weeks_needed * 7
                    end_date = base_date + timedelta(days=days_needed)
                    
                    self.calculation_notes = (
                        f"Working hours service: {service_hours} hours from {base_date_str}, "
                        f"Weekly working hours: {weekly_hours}, "
                        f"Calculated duration: {weeks_needed:.1f} weeks ({days_needed:.0f} days)"
                    )
                else:
                    # Fallback
                    weeks_needed = service_hours / 40
                    days_needed = weeks_needed * 7
                    end_date = base_date + timedelta(days=days_needed)
                    
                    self.calculation_notes = (
                        f"Working hours service: {service_hours} hours from {base_date_str}, "
                        f"Default 40 hours/week used, "
                        f"Calculated duration: {weeks_needed:.1f} weeks ({days_needed:.0f} days)"
                    )
                    
            except AttributeError:
                # Customer has no working hours configured
                weeks_needed = service_hours / 40
                days_needed = weeks_needed * 7
                end_date = base_date + timedelta(days=days_needed)
                
                self.calculation_notes = (
                    f"Working hours service: {service_hours} hours from {base_date_str}, "
                    f"Default 40 hours/week used (no working hours configured), "
                    f"Calculated duration: {weeks_needed:.1f} weeks ({days_needed:.0f} days)"
                )
        
        else:
            # Default fallback
            end_date = base_date + timedelta(days=90)  # 3 months default
            self.calculation_notes = f"Default 3 month service interval applied from {base_date_str}"
        
        return end_date

    @property
    def is_due(self):
        """Check if service is due"""
        return self.next_service_date and datetime.now().date() >= self.next_service_date and not self.is_completed

    @property
    def days_until_due(self):
        """Get days until service is due"""
        if not self.is_completed and self.next_service_date:
            delta = self.next_service_date - datetime.now().date()
            return delta.days
        return None

    def mark_completed(self):
        """Mark service as completed"""
        self.is_completed = True
        self.completed_date = datetime.now().date()
        self.save()

    @classmethod
    def create_service_followups(cls, installation):
        """
        Create service follow-ups based on item master service values.
        This method should be called after installation is saved.
        """
        item_master = installation.inventory_item.name  # name is the ItemMaster FK
        
        # Get all maintenance schedules for this item from the database
        maintenance_schedules = item_master.maintenance_schedules.all()
        
        if maintenance_schedules.exists():
            # Create service follow-ups based on database values
            for schedule in maintenance_schedules:
                # Map database service types to model choices
                service_type_map = {
                    'Periyodik Bakım - Ay Bazlı': 'time_term',
                    'Çalışma Bazlı Periyodik Bakım': 'working_hours',
                    'Ay Bazlı': 'time_term',
                    'Saat Bazlı': 'working_hours'
                }
                
                period_type = schedule.service_period_value.service_period_type.type
                service_type = service_type_map.get(period_type, 'time_term')
                service_value = schedule.service_period_value.value
                
                cls.objects.get_or_create(
                    installation=installation,
                    service_type=service_type,
                    service_value=service_value,
                    defaults={
                        'calculation_notes': f"Database service interval: {service_value} {schedule.service_period_value.service_period_type.unit} ({period_type})"
                    }
                )
        else:
            # Fallback to default service intervals if no database values
            default_services = [
                {'type': 'time_term', 'value': 6, 'type_name': 'Ay'},  # 6 months
                {'type': 'working_hours', 'value': 1000, 'type_name': 'Çalışma Saati'},  # 1000 hours
            ]
            
            for service_config in default_services:
                cls.objects.get_or_create(
                    installation=installation,
                    service_type=service_config['type'],
                    service_value=service_config['value'],
                    defaults={
                        'calculation_notes': f"Default service interval: {service_config['value']} {service_config['type_name']} (veritabanında service tanımı bulunamadı)"
                    }
                )


class MaintenanceRecord(models.Model):
    """
    Ana bakım kaydı modeli - ServiceFollowUp'ı genişletir
    """
    MAINTENANCE_TYPE_CHOICES = [
        ('periodic', 'Periodic Maintenance'),
        ('breakdown', 'Breakdown Maintenance'),
    ]

    service_followup = models.OneToOneField(
        ServiceFollowUp,
        on_delete=models.CASCADE,
        related_name='maintenance_record',
        verbose_name="Service Follow-Up"
    )
    
    # Bakım türü (choice field)
    maintenance_type = models.CharField(
        max_length=20,
        choices=MAINTENANCE_TYPE_CHOICES,
        verbose_name="Maintenance Type",
        help_text="Select the type of maintenance performed"
    )
    
    # Teknisyen (otomatik user bilgisi)
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Technician"
    )
    
    # Arıza sebebi (sadece breakdown maintenance için)
    breakdown_reason = models.TextField(
        blank=True,
        verbose_name="Breakdown Reason",
        help_text="Required for breakdown maintenance"
    )
    
    # Notlar
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    
    # Bakım tarihi
    service_date = models.DateField(
        verbose_name="Service Date",
        help_text="Date when maintenance was performed"
    )
    
    maintenance_date = models.DateField(
        auto_now_add=True,
        verbose_name="Maintenance Date"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Maintenance Record"
        verbose_name_plural = "Maintenance Records"
        ordering = ['-maintenance_date']

    def __str__(self):
        maintenance_type_display = self.get_maintenance_type_display() if self.maintenance_type else "Unknown"
        technician_name = f"{self.technician.first_name} {self.technician.last_name}".strip() if self.technician else "Unknown"
        date_str = self.maintenance_date.strftime('%d.%m.%Y') if self.maintenance_date else 'N/A'
        
        return f"{maintenance_type_display} - {technician_name} ({date_str})"

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Maintenance type is required
        if not self.maintenance_type:
            raise ValidationError("Maintenance type must be selected.")
        
        # Breakdown maintenance için arıza sebebi zorunlu
        if self.maintenance_type == 'breakdown' and not self.breakdown_reason:
            raise ValidationError("Breakdown reason is required for breakdown maintenance.")

    def save(self, *args, **kwargs):
        self.clean()
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # Handle service follow-up logic for periodic maintenance
        if is_new and self.maintenance_type == 'periodic':
            self.handle_periodic_maintenance_completion()

    def handle_periodic_maintenance_completion(self):
        """
        Handle service follow-up logic when periodic maintenance is completed.
        Similar to Installation model's logic.
        """
        from datetime import datetime, timedelta
        
        installation = self.service_followup.installation
        
        # Mark current service as completed
        current_service = self.service_followup
        current_service.is_completed = True
        current_service.completed_date = timezone.now().date()
        current_service.completion_notes = f"Maintenance completed - {self.maintenance_type}"
        current_service.save()
        
        # Create new service follow-up based on the same service type and value
        if current_service.service_type == 'time_term':
            # Time-based service: current service date + months
            try:
                # Parse service_date if it's a string
                if isinstance(self.service_date, str):
                    from datetime import datetime
                    service_date = datetime.strptime(self.service_date, '%Y-%m-%d').date()
                else:
                    service_date = self.service_date
                
                if not service_date:
                    raise ValueError("No service date available")
                
                months = int(current_service.service_value)
                next_service_date = service_date + timedelta(days=months * 30)
                
                service_date_str = service_date.strftime('%d.%m.%Y') if service_date else 'N/A'
                calculation_notes = f"Time-term service: {months} month(s) from last maintenance date ({service_date_str})"
                
            except Exception:
                # Fallback to current date + months
                months = int(current_service.service_value)
                next_service_date = timezone.now().date() + timedelta(days=months * 30)
                calculation_notes = f"Time-term service: {months} month(s) from current date (fallback)"
                
        elif current_service.service_type == 'working_hours':
            # Working hours-based service
            service_hours = float(current_service.service_value)
            
            try:
                working_hours = installation.customer.working_hours
                weekly_hours = working_hours.weekly_working_hours
                
                if weekly_hours > 0:
                    weeks_needed = service_hours / weekly_hours
                    days_needed = weeks_needed * 7
                    
                    # Calculate from service date
                    if isinstance(self.service_date, str):
                        service_date = datetime.strptime(self.service_date, '%Y-%m-%d').date()
                    else:
                        service_date = self.service_date
                    
                    if not service_date:
                        raise ValueError("No service date available")
                        
                    next_service_date = service_date + timedelta(days=days_needed)
                    
                    service_date_str = service_date.strftime('%d.%m.%Y') if service_date else 'N/A'
                    calculation_notes = (
                        f"Working hours service: {service_hours} hours, "
                        f"Weekly working hours: {weekly_hours}, "
                        f"From last maintenance: {service_date_str}"
                    )
                else:
                    # Fallback: 6 months
                    next_service_date = timezone.now().date() + timedelta(days=180)
                    calculation_notes = "Working hours service fallback: 6 months (no working hours data)"
                    
            except Exception:
                # Fallback: 6 months from current date
                next_service_date = timezone.now().date() + timedelta(days=180)
                calculation_notes = "Working hours service fallback: 6 months (calculation error)"
        
        # Create new service follow-up
        ServiceFollowUp.objects.create(
            installation=installation,
            service_type=current_service.service_type,
            service_value=current_service.service_value,
            next_service_date=next_service_date,
            calculation_notes=calculation_notes
        )

    def send_maintenance_notification(self):
        """Bakım tamamlandığında mail gönder"""
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.template.loader import render_to_string
            from django.conf import settings
            
            # Mail content
            context = {
                'maintenance_record': self,
                'maintenance': self,  # Template compatibility
                'installation': self.service_followup.installation,
                'customer': self.service_followup.installation.customer,
                'service_forms': self.service_forms.all(),
                'spare_parts': self.spare_parts.all(),
                'photos': self.photos.all(),
                'documents': self.documents.all(),
                'technician_name': f"{self.technician.first_name} {self.technician.last_name}".strip() if self.technician else "Unknown",
                'maintenance_type_display': self.get_maintenance_type_display() if self.maintenance_type else "Unknown",
                'current_date': timezone.now().strftime('%d.%m.%Y %H:%M'),
                'service_date_formatted': self.service_date if isinstance(self.service_date, str) else self.service_date.strftime('%d.%m.%Y') if self.service_date else 'N/A',
                'language': 'tr'
            }
            
            subject = f"Maintenance Completed - {self.service_followup.installation.inventory_item.name.name}"
            
            # HTML mail template
            html_content = render_to_string('warranty_and_services/emails/maintenance_notification.html', context)
            
            # Recipients - Use same logic as installation notification
            recipients = set()
            
            # 1. Servis yapılan firma maili
            if self.service_followup.installation.customer and self.service_followup.installation.customer.email:
                recipients.add(self.service_followup.installation.customer.email)
            
            # 2. ContactPerson - servis yapılan firmadaki iletişim kişileri
            if hasattr(self.service_followup.installation.customer, 'contactperson_set'):
                for contact in self.service_followup.installation.customer.contactperson_set.all():
                    if contact.email:
                        recipients.add(contact.email)
            
            # 3. Servis yapan user
            if self.technician and self.technician.email:
                recipients.add(self.technician.email)
            
            # 4. Servis yapan firmanın manager ve servis personeli
            if self.technician.company:
                for u in self.technician.company.customuser_set.filter(role__in=[
                    'manager_main', 'salesmanager_main', 'service_main',
                    'manager_distributor', 'salesmanager_distributor', 'service_distributor']):
                    if u.email:
                        recipients.add(u.email)
                
                # 5. Related manager
                if self.technician.company.related_manager and self.technician.company.related_manager.email:
                    recipients.add(self.technician.company.related_manager.email)
            
            if recipients:
                email = EmailMultiAlternatives(
                    subject,
                    html_content,
                    settings.DEFAULT_FROM_EMAIL,
                    list(recipients)
                )
                email.attach_alternative(html_content, "text/html")
                
                # PDF generation completely disabled for performance
                pdf_buffer = None
                # Note: PDF attachment temporarily disabled to improve response time
                # Users will receive detailed HTML email instead
                
                # PDF attachment - only if PDF was generated successfully
                if pdf_buffer:
                    date_str = self.service_date.strftime('%d%m%Y') if self.service_date else 'unknown'
                    filename = f"bakim_raporu_{self.service_followup.installation.inventory_item.serial_no}_{date_str}.pdf"
                    email.attach(filename, pdf_buffer.read(), 'application/pdf')
                
                email.send()
                print(f"✅ Maintenance notification email sent to: {list(recipients)}")
                if pdf_buffer:
                    print("📎 PDF attachment included")
                else:
                    print("📧 Email sent without PDF attachment")
                
            else:
                print("❌ No recipients found for maintenance notification email")
                
        except Exception as e:
            print(f"❌ Error sending maintenance notification email: {e}")
            import traceback
            traceback.print_exc()
            raise e


class MaintenanceServiceForm(models.Model):
    """
    Bakım sırasında yapılan kontrol formları
    """
    maintenance_record = models.ForeignKey(
        MaintenanceRecord,
        on_delete=models.CASCADE,
        related_name='service_forms',
        verbose_name="Maintenance Record"
    )
    service_form = models.ForeignKey(
        'item_master.ServiceForm',
        on_delete=models.CASCADE,
        verbose_name="Service Form"
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Completed"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Maintenance Service Form"
        verbose_name_plural = "Maintenance Service Forms"
        unique_together = ('maintenance_record', 'service_form')

    def __str__(self):
        status = "✓" if self.is_completed else "⏳"
        return f"{status} {self.service_form.name}"


class MaintenanceSparePart(models.Model):
    """
    Bakım sırasında kullanılan yedek parçalar
    """
    maintenance_record = models.ForeignKey(
        MaintenanceRecord,
        on_delete=models.CASCADE,
        related_name='spare_parts',
        verbose_name="Maintenance Record"
    )
    spare_part = models.ForeignKey(
        'item_master.ItemMaster',
        on_delete=models.CASCADE,
        verbose_name="Spare Part"
    )
    is_used = models.BooleanField(
        default=False,
        verbose_name="Used"
    )
    quantity_used = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantity Used"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Maintenance Spare Part"
        verbose_name_plural = "Maintenance Spare Parts"
        unique_together = ('maintenance_record', 'spare_part')

    def __str__(self):
        status = "✓" if self.is_used else "⏳"
        qty = f" (x{self.quantity_used})" if self.is_used and self.quantity_used > 1 else ""
        return f"{status} {self.spare_part.name}{qty}"


class MaintenancePhoto(models.Model):
    """
    Bakım fotoğrafları
    """
    maintenance_record = models.ForeignKey(
        MaintenanceRecord,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name="Maintenance Record"
    )
    image = models.ImageField(
        upload_to='maintenance_photos/',
        verbose_name="Photo"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Description"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Maintenance Photo"
        verbose_name_plural = "Maintenance Photos"
        ordering = ['created_at']

    def __str__(self):
        return f"Photo {self.id} - {self.maintenance_record}"


class MaintenanceDocument(models.Model):
    """
    Bakım belgeleri
    """
    maintenance_record = models.ForeignKey(
        MaintenanceRecord,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Maintenance Record"
    )
    document = models.FileField(
        upload_to='maintenance_documents/',
        verbose_name="Document"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Document Name"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Description"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Maintenance Document"
        verbose_name_plural = "Maintenance Documents"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} - {self.maintenance_record}"
