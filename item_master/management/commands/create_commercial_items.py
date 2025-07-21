from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.core.files import File
from item_master.models import (
    Category, Brand, StockType, Status, ItemMaster, ItemImage,
    WarrantyType, WarrantyValue, ServiceForm, ItemSparePart,
    InventoryItem
)
import os
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create commercial item masters with warranties, spare parts, and service forms'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing commercial item masters before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing commercial item masters...')
            # Only clear commercial items (Ticari stock type)
            try:
                ticari_stock_type = StockType.objects.get(name="Ticari")
                ItemMaster.objects.filter(stock_type=ticari_stock_type).delete()
                self.stdout.write(
                    self.style.SUCCESS('Successfully cleared commercial item masters')
                )
            except StockType.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING('Ticari stock type not found, nothing to clear')
                )

        # Create/Get required dependencies
        self.create_dependencies()
        
        # Get required objects for relationships
        try:
            spare_parts = self.get_spare_parts()
            warranties = self.get_warranties()
            service_forms = self.get_service_forms()
            admin_user = self.get_admin_user()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error getting dependencies: {str(e)}')
            )
            return

        # Commercial Item Masters data
        items_data = [
            # OSC T Series
            {"code": "OSC 3  T", "name": "OSC 3  T Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 4 T", "name": "OSC 4 T Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 5 T", "name": "OSC 5 T Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 7 T", "name": "OSC 7 T Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 11 T", "name": "OSC 11 T Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 15 T", "name": "OSC 15 T Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 18 T", "name": "OSC 18 T Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 22 T", "name": "OSC 22 T Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 30 T", "name": "OSC 30 T Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            
            # OSC TD Series
            {"code": "OSC 3  TD", "name": "OSC 3  TD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 4 TD", "name": "OSC 4 TD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 5 TD", "name": "OSC 5 TD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 7 TD", "name": "OSC 7 TD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 11 TD", "name": "OSC 11 TD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 15 TD", "name": "OSC 15 TD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 18 TD", "name": "OSC 18 TD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 22 TD", "name": "OSC 22 TD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 30 TD", "name": "OSC 30 TD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            
            # OSC VT Series
            {"code": "OSC 3  VT", "name": "OSC 3  VT Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 4 VT", "name": "OSC 4 VT Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 5 VT", "name": "OSC 5 VT Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 7 VT", "name": "OSC 7 VT Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 11 VT", "name": "OSC 11 VT Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 15 VT", "name": "OSC 15 VT Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 18 VT", "name": "OSC 18 VT Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 22 VT", "name": "OSC 22 VT Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 30 VT", "name": "OSC 30 VT Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            
            # OSC VTD Series
            {"code": "OSC 3  VTD", "name": "OSC 3  VTD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 4 VTD", "name": "OSC 4 VTD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 5 VTD", "name": "OSC 5 VTD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 7 VTD", "name": "OSC 7 VTD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 11 VTD", "name": "OSC 11 VTD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 15 VTD", "name": "OSC 15 VTD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 18 VTD", "name": "OSC 18 VTD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 22 VTD", "name": "OSC 22 VTD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            {"code": "OSC 30 VTD", "name": "OSC 30 VTD Tank Üstü Vidalı Kompresör", "category": "OSC T Serisi", "stock_qty": 1},
            
            # OSC U Series
            {"code": "OSC 30 U", "name": "OSC 30 U Direkt Akuple Vidalı Kompresör", "category": "OSC U, OSC D Serisi", "stock_qty": 1},
            {"code": "OSC 37 U", "name": "OSC 37 U Direkt Akuple Vidalı Kompresör", "category": "OSC U, OSC D Serisi", "stock_qty": 1},
            {"code": "OSC 45 U", "name": "OSC 45 U Direkt Akuple Vidalı Kompresör", "category": "OSC U, OSC D Serisi", "stock_qty": 1},
            {"code": "OSC 55 U", "name": "OSC 55 U Direkt Akuple Vidalı Kompresör", "category": "OSC U, OSC D Serisi", "stock_qty": 1},
            {"code": "OSC 75 U", "name": "OSC 75 U Direkt Akuple Vidalı Kompresör", "category": "OSC U, OSC D Serisi", "stock_qty": 1},
            {"code": "OSC 90 U", "name": "OSC 90 U Direkt Akuple Vidalı Kompresör", "category": "OSC U, OSC D Serisi", "stock_qty": 1},
            
            # TK Series (Pistonlu)
            {"code": "TK-100/70 M", "name": "TK-100/70 M Pistonlu Kompresör", "category": "Tek Kademeli Kompresörler", "stock_qty": 1},
            {"code": "TK-100/70", "name": "TK-100/70  Pistonlu Kompresör", "category": "Tek Kademeli Kompresörler", "stock_qty": 1},
            {"code": "TK-150/2X60 M", "name": "TK-150/2X60 M  Pistonlu Kompresör", "category": "Tek Kademeli Kompresörler", "stock_qty": 1},
            {"code": "TK-150/2X60", "name": "TK-150/2X60  Pistonlu Kompresör", "category": "Tek Kademeli Kompresörler", "stock_qty": 1},
            {"code": "TK-200/2X70 M", "name": "TK-200/2X70 M Pistonlu Kompresör", "category": "Tek Kademeli Kompresörler", "stock_qty": 1},
            {"code": "TK-200/2X70", "name": "TK-200/2X70  Pistonlu Kompresör", "category": "Tek Kademeli Kompresörler", "stock_qty": 1},
            {"code": "TK-200/2X70-3", "name": "TK-200/2X70-3  Pistonlu Kompresör", "category": "Tek Kademeli Kompresörler", "stock_qty": 1},
            {"code": "TK-300/2X90", "name": "TK-300/2X90  Pistonlu Kompresör", "category": "Tek Kademeli Kompresörler", "stock_qty": 1},
            {"code": "TK-300/2X91-5*", "name": "TK-300/2X91-5*  Pistonlu Kompresör", "category": "Tek Kademeli Kompresörler", "stock_qty": 1},
            {"code": "TK-500/2X91- 5", "name": "TK-500/2X91- 5  Pistonlu Kompresör", "category": "Tek Kademeli Kompresörler", "stock_qty": 1},
            {"code": "TK-500/2X110*", "name": "TK-500/2X110* Pistonlu Kompresör", "category": "Tek Kademeli Kompresörler", "stock_qty": 1},
            {"code": "TK-500/3X90*", "name": "TK-500/3X90*  Pistonlu Kompresör", "category": "Tek Kademeli Kompresörler", "stock_qty": 1},
            {"code": "TK-500/3X110*", "name": "TK-500/3X110*  Pistonlu Kompresör", "category": "Tek Kademeli Kompresörler", "stock_qty": 1},
            {"code": "TK-500/3X110", "name": "TK-500/3X110 Pistonlu Kompresör", "category": "Tek Kademeli Kompresörler", "stock_qty": 1},
        ]

        created_items = 0
        updated_items = 0

        for item_data in items_data:
            try:
                # Get required objects
                category = Category.objects.get(category_name=item_data['category'])
                brand = Brand.objects.get(name="Özen")
                stock_type = StockType.objects.get(name="Ticari")
                status = Status.objects.get(status="Kullanımda")

                # Create or update ItemMaster
                item_master, created = ItemMaster.objects.get_or_create(
                    shortcode=item_data['code'],
                    defaults={
                        'name': item_data['name'],
                        'category': category,
                        'brand_name': brand,
                        'stock_type': stock_type,
                        'status': status,
                        'slug': slugify(item_data['name']),
                        'description': f'{item_data["name"]} - {item_data["category"]}'
                    }
                )

                if created:
                    created_items += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created item master: {item_data["code"]} - {item_data["name"]}')
                    )
                else:
                    # Update existing item
                    item_master.name = item_data['name']
                    item_master.category = category
                    item_master.brand_name = brand
                    item_master.stock_type = stock_type
                    item_master.status = status
                    item_master.slug = slugify(item_data['name'])
                    item_master.description = f'{item_data["name"]} - {item_data["category"]}'
                    item_master.save()
                    updated_items += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated item master: {item_data["code"]} - {item_data["name"]}')
                    )

                # Add relationships
                self.add_relationships(item_master, warranties, spare_parts, service_forms)
                
                # Create inventory item with specified quantity
                self.create_inventory_item(item_master, item_data['stock_qty'], admin_user)

                # Note about image
                self.stdout.write(
                    self.style.WARNING(f'Note: Please add image "ozen-kopmresor-osc--t-serisi.jpg" for {item_data["code"]}')
                )

            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Category not found: {item_data["category"]}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating {item_data["code"]}: {str(e)}')
                )

        self.stdout.write('\n')
        self.stdout.write(
            self.style.SUCCESS(
                f'Commercial Item Masters creation completed!\n'
                f'Created: {created_items}\n'
                f'Updated: {updated_items}\n'
                f'Total items in database: {ItemMaster.objects.count()}'
            )
        )

    def create_dependencies(self):
        """Create required dependencies"""
        
        # Create brand
        brand, created = Brand.objects.get_or_create(
            name="Özen",
            defaults={'name': 'Özen'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created brand: Özen'))

        # Create stock types
        stock_types = ["Ticari", "Yedek Parça"]
        for stock_type_name in stock_types:
            stock_type, created = StockType.objects.get_or_create(
                name=stock_type_name,
                defaults={'name': stock_type_name}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created stock type: {stock_type_name}'))

        # Create status
        status, created = Status.objects.get_or_create(
            status="Kullanımda",
            defaults={'status': 'Kullanımda'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created status: Kullanımda'))

        # Create warranty types and values if they don't exist
        warranty_types_data = [
            {"type": "Standart Garanti", "value": 12.0},
            {"type": "Uzatılmış Garanti", "value": 24.0}
        ]
        
        for warranty_data in warranty_types_data:
            warranty_type, created = WarrantyType.objects.get_or_create(
                type=warranty_data["type"],
                defaults={'type': warranty_data["type"]}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created warranty type: {warranty_data["type"]}'))
            
            warranty_value, created = WarrantyValue.objects.get_or_create(
                warranty_type=warranty_type,
                value=warranty_data["value"],
                defaults={
                    'warranty_type': warranty_type,
                    'value': warranty_data["value"]
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created warranty value: {warranty_data["type"]} - {warranty_data["value"]} months'))

        # Create service forms if they don't exist
        service_forms_data = [
            "Kurulum Formu",
            "Bakım Formu", 
            "Onarım Formu",
            "Garanti Formu"
        ]
        
        for service_form_name in service_forms_data:
            service_form, created = ServiceForm.objects.get_or_create(
                name=service_form_name,
                defaults={'name': service_form_name}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created service form: {service_form_name}'))

        self.stdout.write('\n--- Dependencies created successfully ---\n')

    def get_spare_parts(self):
        """Get all spare parts (Yedek Parça stock type items)"""
        try:
            spare_part_stock_type = StockType.objects.get(name="Yedek Parça")
            return ItemMaster.objects.filter(stock_type=spare_part_stock_type)
        except StockType.DoesNotExist:
            self.stdout.write(self.style.WARNING('Yedek Parça stock type not found'))
            return ItemMaster.objects.none()

    def get_warranties(self):
        """Get all warranty values"""
        return WarrantyValue.objects.all()

    def get_service_forms(self):
        """Get all service forms"""
        return ServiceForm.objects.all()

    def get_admin_user(self):
        """Get or create admin user for inventory items"""
        try:
            # Try to get superuser
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                return admin_user
            
            # Try to get any user
            user = User.objects.first()
            if user:
                return user
            
            # Create a default user if none exists
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@example.com',
                password='admin123',
                is_superuser=True,
                is_staff=True
            )
            self.stdout.write(self.style.WARNING('Created default admin user for inventory items'))
            return admin_user
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting admin user: {str(e)}'))
            return None

    def add_relationships(self, item_master, warranties, spare_parts, service_forms):
        """Add warranties, spare parts, and service forms to item master"""
        
        # Add all warranties
        for warranty in warranties:
            item_master.warranties.add(warranty)
        
        # Add all service forms
        for service_form in service_forms:
            item_master.service_forms.add(service_form)
        
        # Add all spare parts through ItemSparePart model
        for spare_part in spare_parts:
            ItemSparePart.objects.get_or_create(
                main_item=item_master,
                spare_part_item=spare_part
            )

    def create_inventory_item(self, item_master, quantity, admin_user):
        """Create inventory item with specified quantity"""
        if admin_user:
            for i in range(quantity):
                inventory_item, created = InventoryItem.objects.get_or_create(
                    name=item_master,
                    serial_no=f"{item_master.shortcode}-{i+1:03d}",
                    defaults={
                        'quantity': 1,
                        'created_by': admin_user,
                        'in_used': False
                    }
                )
                if created:
                    # Generate QR code
                    inventory_item.generate_qr_code()
                    inventory_item.save()
