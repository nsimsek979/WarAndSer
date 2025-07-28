from django.core.management.base import BaseCommand
from ...models import (
    InventoryItem,
    InventoryItemAttribute,
    AttributeType,
    AttributeUnit,
    AttributeTypeUnit
)
import random

class Command(BaseCommand):
    help = 'Creates random inventory item attributes for each inventory item'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing attributes before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted_count = InventoryItemAttribute.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing attributes'))

        # Get or create attribute types and units
        attribute_configs = {
            'power': {
                'units': [
                    {'name': 'Kilowatt', 'symbol': 'kW', 'range': (4.0, 7.5)},
                    {'name': 'HP', 'symbol': 'HPP', 'range': (3, 5)}
                ],
                'description': 'Motor power rating'
            },
            'pressure': {
                'units': [
                    {'name': 'Bar', 'symbol': 'bar', 'range': (5.5, 15.0)}
                ],
                'description': 'Working pressure'
            },
            'capacity': {
                'units': [
                    {'name': 'Litre/Dakika', 'symbol': 'lt/dak', 'range': (420, 620)}
                ],
                'description': 'Air flow capacity'
            },
            'tank_volume': {
                'units': [
                    {'name': 'Litre', 'symbol': 'lt', 'range': (300, 500)}
                ],
                'description': 'Tank volume capacity'
            },
            'weight': {
                'units': [
                    {'name': 'Kilogram', 'symbol': 'Kg', 'range': (245, 550)}
                ],
                'description': 'Total weight'
            }
        }

        # Create AttributeType and AttributeUnit records
        for attr_name, config in attribute_configs.items():
            # Create or get AttributeType
            attr_type, created = AttributeType.objects.get_or_create(
                name=attr_name,
                defaults={
                    'description': config['description'],
                    'is_required': False
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created AttributeType: {attr_name}'))

            # Create or get AttributeUnits
            for unit_config in config['units']:
                unit, created = AttributeUnit.objects.get_or_create(
                    name=unit_config['name'],
                    defaults={'symbol': unit_config['symbol']}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created AttributeUnit: {unit}'))
                else:
                    # Update symbol if it's different (in case of existing records)
                    if unit.symbol != unit_config['symbol']:
                        unit.symbol = unit_config['symbol']
                        unit.save()
                        self.stdout.write(self.style.WARNING(f'Updated AttributeUnit symbol: {unit}'))
                
                # Create relationship between AttributeType and AttributeUnit
                type_unit, created = AttributeTypeUnit.objects.get_or_create(
                    attribute_type=attr_type,
                    attribute_unit=unit,
                    defaults={'is_default': True}  # Make first unit default for each type
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created AttributeTypeUnit: {type_unit}'))

        # Get all inventory items
        inventory_items = InventoryItem.objects.all()
        
        if not inventory_items.exists():
            self.stdout.write(self.style.ERROR('No inventory items found'))
            return

        created_count = 0

        for item in inventory_items:
            # Randomly assign 2-4 attributes per item
            num_attributes = random.randint(2, 4)
            selected_attributes = random.sample(list(attribute_configs.keys()), num_attributes)
            
            for attr_name in selected_attributes:
                config = attribute_configs[attr_name]
                
                # Randomly select a unit for this attribute
                unit_config = random.choice(config['units'])
                
                try:
                    # Get the AttributeType and AttributeUnit objects
                    attr_type = AttributeType.objects.get(name=attr_name)
                    unit = AttributeUnit.objects.get(name=unit_config['name'])
                    
                    # Generate random value based on range
                    min_val, max_val = unit_config['range']
                    
                    if attr_name in ['power', 'pressure']:
                        # Float values with 1-2 decimal places
                        value = round(random.uniform(min_val, max_val), 2)
                    else:
                        # Integer values
                        value = random.randint(int(min_val), int(max_val))
                    
                    # Create the inventory item attribute
                    InventoryItemAttribute.objects.create(
                        inventory_item=item,
                        attribute_type=attr_type,
                        value=str(value),
                        unit=unit,
                        notes=f"Auto-generated {attr_name} specification"
                    )
                    
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'Created {attr_name} ({unit.symbol}) = {value} for {item}'
                    ))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'Failed to create {attr_name} attribute for {item}: {str(e)}'
                    ))

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {created_count} inventory item attributes'
        ))