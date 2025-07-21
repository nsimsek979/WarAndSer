from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.core.files import File
from item_master.models import (
    Category, Brand, StockType, Status, ItemMaster, ItemImage
)
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Create item masters with required dependencies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing item masters before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing item masters...')
            ItemMaster.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared all item masters')
            )

        # Create/Get required dependencies
        self.create_dependencies()
        
        # Item Masters data
        items_data = [
            {
                "code": "EVTK",
                "name": "Emiş Valfi Tamir Kiti",
                "category": "Emiş Valfi Tamir Kitleri",
                "brand": "Özen",
                "stock_type": "Yedek Parça",
                "status": "Kullanımda",
                "image": "statics/valf-tamir-takimi"
            },
            {
                "code": "MBBVK",
                "name": "Minimum Basınç Valfi Tamir Kiti",
                "category": "Minimum Basınç Valfi Tamir Kitleri",
                "brand": "Özen",
                "stock_type": "Yedek Parça",
                "status": "Kullanımda",
                "image": "statics/basınc valfı kiti"
            },
            {
                "code": "TVTK",
                "name": "Termostatik Valf Tamir Kiti",
                "category": "Termostatik Valf Tamir Kitleri",
                "brand": "Özen",
                "stock_type": "Yedek Parça",
                "status": "Kullanımda",
                "image": "statics/Termostatikvalf"
            },
            {
                "code": "HH",
                "name": "Hidrolik Hortumlar",
                "category": "Hidrolik Hortumlar",
                "brand": "Özen",
                "stock_type": "Yedek Parça",
                "status": "Kullanımda",
                "image": "statics/hidrolik-hortum"
            },
            {
                "code": "BS",
                "name": "Basınç Sensörleri ve Basınç prosestatları",
                "category": "Basınç Sensörleri ve Basınç prosestatları",
                "brand": "Özen",
                "stock_type": "Yedek Parça",
                "status": "Kullanımda",
                "image": "statics/basinc-sensoru"
            },
            {
                "code": "PLC",
                "name": "Kompresör Plc Üniteleri",
                "category": "Kompresör Plc Üniteleri",
                "brand": "Özen",
                "stock_type": "Yedek Parça",
                "status": "Kullanımda",
                "image": "statics/plc"
            },
            {
                "code": "SF",
                "name": "Seperatör Filtreleri",
                "category": "Seperatör Filtreleri",
                "brand": "Özen",
                "stock_type": "Yedek Parça",
                "status": "Kullanımda",
                "image": "statics/seperatörfiltre"
            },
            {
                "code": "YF",
                "name": "Yağ Filtreleri",
                "category": "Yağ Filtreleri",
                "brand": "Özen",
                "stock_type": "Yedek Parça",
                "status": "Kullanımda",
                "image": "statics/yagfiltre"
            },
            {
                "code": "HF",
                "name": "Hava Filtreleri",
                "category": "Hava Filtreleri",
                "brand": "Özen",
                "stock_type": "Yedek Parça",
                "status": "Kullanımda",
                "image": "statics/hava-filtreleri"
            },
            {
                "code": "OILSTOP",
                "name": "Oil Stop Valfi Tamir Kitleri",
                "category": "Oil Stop Valfi Tamir Kitleri",
                "brand": "Özen",
                "stock_type": "Yedek Parça",
                "status": "Kullanımda",
                "image": "statics/stop"
            }
        ]

        created_items = 0
        updated_items = 0

        for item_data in items_data:
            try:
                # Get required objects
                category = Category.objects.get(category_name=item_data['category'])
                brand = Brand.objects.get(name=item_data['brand'])
                stock_type = StockType.objects.get(name=item_data['stock_type'])
                status = Status.objects.get(status=item_data['status'])

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

                # Create ItemImage if image path is provided
                if item_data.get('image'):
                    # Check if image already exists for this item
                    if not ItemImage.objects.filter(item=item_master).exists():
                        # Note: The image files should be placed in the media folder manually
                        # This just creates the database record with the path
                        self.stdout.write(
                            self.style.WARNING(f'Note: Image path noted for {item_data["code"]}: {item_data["image"]}')
                        )
                        self.stdout.write(
                            self.style.WARNING(f'Please manually add the image file and create ItemImage record in admin')
                        )

            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Category not found: {item_data["category"]}')
                )
            except Brand.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Brand not found: {item_data["brand"]}')
                )
            except StockType.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Stock Type not found: {item_data["stock_type"]}')
                )
            except Status.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Status not found: {item_data["status"]}')
                )

        self.stdout.write('\n')
        self.stdout.write(
            self.style.SUCCESS(
                f'Item Masters creation completed!\n'
                f'Created: {created_items}\n'
                f'Updated: {updated_items}\n'
                f'Total items in database: {ItemMaster.objects.count()}'
            )
        )

    def create_dependencies(self):
        """Create required categories, brand, stock type, and status"""
        
        # Create brand
        brand, created = Brand.objects.get_or_create(
            name="Özen",
            defaults={'name': 'Özen'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created brand: Özen'))
        else:
            self.stdout.write(self.style.WARNING('Brand already exists: Özen'))

        # Create stock type
        stock_type, created = StockType.objects.get_or_create(
            name="Yedek Parça",
            defaults={'name': 'Yedek Parça'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created stock type: Yedek Parça'))
        else:
            self.stdout.write(self.style.WARNING('Stock type already exists: Yedek Parça'))

        # Create status
        status, created = Status.objects.get_or_create(
            status="Kullanımda",
            defaults={'status': 'Kullanımda'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created status: Kullanımda'))
        else:
            self.stdout.write(self.style.WARNING('Status already exists: Kullanımda'))

        # Create categories
        categories = [
            "Emiş Valfi Tamir Kitleri",
            "Minimum Basınç Valfi Tamir Kitleri", 
            "Termostatik Valf Tamir Kitleri",
            "Hidrolik Hortumlar",
            "Basınç Sensörleri ve Basınç prosestatları",
            "Kompresör Plc Üniteleri",
            "Seperatör Filtreleri",
            "Yağ Filtreleri",
            "Hava Filtreleri",
            "Oil Stop Valfi Tamir Kitleri"
        ]

        for category_name in categories:
            category, created = Category.objects.get_or_create(
                category_name=category_name,
                defaults={
                    'category_name': category_name,
                    'slug': slugify(category_name),
                    'parent': None  # These are main categories
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Category already exists: {category_name}'))

        self.stdout.write('\n--- Dependencies created successfully ---\n')
