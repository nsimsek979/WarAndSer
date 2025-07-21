from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from item_master.models import ItemMaster, ItemImage, StockType
import os
import random


class Command(BaseCommand):
    help = 'Add images to item masters with stock_type="Ticari" from static folder'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing images before adding new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing item images...')
            ItemImage.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared all item images')
            )

        # Static folder path
        static_dir = os.path.join(settings.BASE_DIR, 'static')
        
        # Specific image for commercial items
        compressor_image = 'ozen-kompresor-osc-t-serisi.jpg'
        image_path = os.path.join(static_dir, compressor_image)
        
        if not os.path.exists(image_path):
            self.stdout.write(
                self.style.ERROR(f'Image not found: {image_path}')
            )
            return

        # Get Ticari stock type
        try:
            ticari_stock_type = StockType.objects.get(name="Ticari")
        except StockType.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Stock type "Ticari" not found. Please create it first.')
            )
            return

        # Get all Ticari items
        commercial_items = ItemMaster.objects.filter(stock_type=ticari_stock_type)
        
        if not commercial_items.exists():
            self.stdout.write(
                self.style.WARNING('No commercial items found with stock_type="Ticari"')
            )
            return

        self.stdout.write(f'Found {commercial_items.count()} commercial items')

        # Add images to commercial items
        images_added = 0
        for item in commercial_items:
            # Check if item already has images
            if not options['clear'] and item.images.exists():
                self.stdout.write(f'Item "{item.name}" already has images, skipping...')
                continue

            try:
                with open(image_path, 'rb') as f:
                    django_file = File(f)
                    
                    item_image = ItemImage.objects.create(item=item)
                    item_image.url.save(
                        compressor_image,
                        django_file,
                        save=True
                    )
                    
                    images_added += 1
                    self.stdout.write(f'Added image to item "{item.name}"')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error adding image to item "{item.name}": {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully added {images_added} images to commercial items')
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully added {images_added} images to commercial items')
        )
