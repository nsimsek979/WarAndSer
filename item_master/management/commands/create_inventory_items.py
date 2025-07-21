from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ...models import (
    ItemMaster,
    InventoryItem,
    StockType,
    AttributeType,
    AttributeUnit,
    InventoryItemAttribute
)
import random
import string
from datetime import datetime, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates random inventory items for Ticari items with attributes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of inventory items to create per ItemMaster (default: 3)'
        )
        parser.add_argument(
            '--username',
            type=str,
            default='nihat',
            help='Username to use as created_by (default: nihat)'
        )

    def handle(self, *args, **options):
        count = options['count']
        username = options['username']
        
        try:
            # Get required objects
            admin_user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
            return
        
        try:
            stock_type_ticari = StockType.objects.get(name='Ticari')
        except StockType.DoesNotExist:
            self.stdout.write(self.style.ERROR('StockType "Ticari" not found'))
            return
        
        # Get all ItemMaster records with stock_type = Ticari
        items = ItemMaster.objects.filter(stock_type=stock_type_ticari)
        
        if not items.exists():
            self.stdout.write(self.style.ERROR('No items with stock_type="Ticari" found'))
            return

        created_count = 0
        
        # Get some attribute types for random assignment
        attribute_types = list(AttributeType.objects.all()[:5])  # Get first 5 attribute types
        units = list(AttributeUnit.objects.all()[:3])  # Get first 3 units
        
        for item in items:
            for i in range(1, count + 1):  # Create specified number of inventory items for each
                try:
                    # Generate random data
                    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    serial_no = f"SN-{item.shortcode}-{random_chars}"
                    
                    # Create inventory item with only existing fields
                    inventory_item = InventoryItem.objects.create(
                        name=item,
                        quantity=random.randint(1, 10),
                        created_by=admin_user,
                        serial_no=serial_no,
                        in_used=random.choice([True, False])
                    )
                    
                    # Add some random attributes if attribute types exist
                    if attribute_types:
                        num_attributes = random.randint(1, min(3, len(attribute_types)))
                        selected_attributes = random.sample(attribute_types, num_attributes)
                        
                        for attr_type in selected_attributes:
                            try:
                                InventoryItemAttribute.objects.create(
                                    inventory_item=inventory_item,
                                    attribute_type=attr_type,
                                    value=f"{random.randint(1, 100)}",
                                    unit=random.choice(units) if units else None,
                                    notes=f"Auto-generated attribute for {item.name}"
                                )
                            except Exception as attr_error:
                                # Skip if attribute creation fails (probably duplicate)
                                pass
                    
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'Created inventory item {serial_no} for {item.name}'
                    ))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'Failed to create inventory item for {item.name}: {str(e)}'
                    ))

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {created_count} inventory items'
        ))