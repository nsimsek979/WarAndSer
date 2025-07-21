from django.core.management.base import BaseCommand
from item_master.models import AttributeType, AttributeUnit, AttributeTypeUnit, InventoryItem, InventoryItemAttribute
import random


class Command(BaseCommand):
    help = 'Create attribute types and units with their relationships, then add them to inventory items with random values'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing attributes before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing attributes...')
            InventoryItemAttribute.objects.all().delete()
            AttributeTypeUnit.objects.all().delete()
            AttributeUnit.objects.all().delete()
            AttributeType.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Successfully cleared all attributes'))

        # Define attribute types and their units
        attribute_data = [
            {
                'type_name': 'Tank Hacmi',
                'units': [{'name': 'Litre', 'symbol': 'lt', 'is_default': True}]
            },
            {
                'type_name': 'Hava Emiş',
                'units': [{'name': 'Litre/Dakika', 'symbol': 'lt/dak', 'is_default': True}]
            },
            {
                'type_name': 'Basınç',
                'units': [
                    {'name': 'Bar', 'symbol': 'bar', 'is_default': True},
                    {'name': 'PSI', 'symbol': 'PSI', 'is_default': False}
                ]
            },
            {
                'type_name': 'Silindir Sayısı',
                'units': [{'name': 'Adet', 'symbol': 'Ad', 'is_default': True}]
            },
            {
                'type_name': 'Silindir Çapı',
                'units': [{'name': 'Milimetre', 'symbol': 'mm', 'is_default': True}]
            },
            {
                'type_name': 'Motor Gücü',
                'units': [
                    {'name': 'HP', 'symbol': 'HP', 'is_default': True},
                    {'name': 'Kilowatt', 'symbol': 'Kw', 'is_default': False}
                ]
            },
            {
                'type_name': 'Ağırlık',
                'units': [{'name': 'Kilogram', 'symbol': 'Kg', 'is_default': True}]
            }
        ]

        # Create attribute types, units, and their relationships
        created_types = {}
        for attr_data in attribute_data:
            # Create or get attribute type
            attr_type, created = AttributeType.objects.get_or_create(
                name=attr_data['type_name'],
                defaults={
                    'description': f'{attr_data["type_name"]} attribute type',
                    'is_required': False
                }
            )
            created_types[attr_type.name] = attr_type
            
            if created:
                self.stdout.write(f'Created attribute type: {attr_type.name}')
            else:
                self.stdout.write(f'Found existing attribute type: {attr_type.name}')

            # Create units and relationships for this attribute type
            for unit_data in attr_data['units']:
                # Create or get the unit
                unit, created = AttributeUnit.objects.get_or_create(
                    name=unit_data['name'],
                    symbol=unit_data['symbol'],
                    defaults={}
                )
                
                if created:
                    self.stdout.write(f'  Created unit: {unit.name} ({unit.symbol})')
                else:
                    self.stdout.write(f'  Found existing unit: {unit.name} ({unit.symbol})')

                # Create the relationship between attribute type and unit
                type_unit, created = AttributeTypeUnit.objects.get_or_create(
                    attribute_type=attr_type,
                    attribute_unit=unit,
                    defaults={'is_default': unit_data.get('is_default', False)}
                )
                
                if created:
                    default_text = " (Default)" if type_unit.is_default else ""
                    self.stdout.write(f'    Linked to {attr_type.name}{default_text}')

        # Add attributes to all inventory items
        inventory_items = InventoryItem.objects.all()
        if not inventory_items.exists():
            self.stdout.write(self.style.WARNING('No inventory items found to add attributes to'))
            return

        self.stdout.write(f'Adding attributes to {inventory_items.count()} inventory items...')

        # Define value ranges for each attribute type
        value_ranges = {
            'Tank Hacmi': (50, 500),          # 50-500 liters
            'Hava Emiş': (100, 2000),        # 100-2000 lt/dak
            'Basınç': (8, 15),               # 8-15 bar or equivalent PSI
            'Silindir Sayısı': (1, 4),       # 1-4 cylinders
            'Silindir Çapı': (50, 150),      # 50-150 mm
            'Motor Gücü': (1, 10),           # 1-10 HP or equivalent Kw
            'Ağırlık': (50, 300)             # 50-300 kg
        }

        attributes_added = 0
        for item in inventory_items:
            for attr_type in created_types.values():
                # Get available units for this attribute type
                available_type_units = AttributeTypeUnit.objects.filter(attribute_type=attr_type)
                if not available_type_units.exists():
                    continue
                
                # Select a random unit (with preference for default)
                default_unit = available_type_units.filter(is_default=True).first()
                if default_unit and random.random() < 0.7:  # 70% chance to use default
                    selected_type_unit = default_unit
                else:
                    selected_type_unit = random.choice(available_type_units)
                
                selected_unit = selected_type_unit.attribute_unit
                
                # Generate random value based on attribute type
                min_val, max_val = value_ranges.get(attr_type.name, (1, 100))
                
                # Adjust values for different units
                if attr_type.name == 'Basınç' and selected_unit.symbol == 'PSI':
                    # Convert bar to PSI (1 bar ≈ 14.5 PSI)
                    value = round(random.uniform(min_val * 14.5, max_val * 14.5), 1)
                elif attr_type.name == 'Motor Gücü' and selected_unit.symbol == 'Kw':
                    # Convert HP to Kw (1 HP ≈ 0.746 Kw)
                    value = round(random.uniform(min_val * 0.746, max_val * 0.746), 2)
                elif attr_type.name == 'Silindir Sayısı':
                    value = random.randint(min_val, max_val)
                else:
                    if attr_type.name in ['Tank Hacmi', 'Hava Emiş', 'Silindir Çapı', 'Ağırlık']:
                        value = random.randint(min_val, max_val)
                    else:
                        value = round(random.uniform(min_val, max_val), 2)

                # Create the attribute
                try:
                    attr, created = InventoryItemAttribute.objects.get_or_create(
                        inventory_item=item,
                        attribute_type=attr_type,
                        unit=selected_unit,
                        defaults={'value': str(value)}
                    )
                    
                    if created:
                        attributes_added += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error creating attribute for item {item.qr_code}: {str(e)}')
                    )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully added {attributes_added} attributes to inventory items')
        )

        # Show summary
        self.stdout.write('\nSummary:')
        for attr_type in created_types.values():
            type_unit_count = AttributeTypeUnit.objects.filter(attribute_type=attr_type).count()
            item_count = InventoryItemAttribute.objects.filter(attribute_type=attr_type).count()
            self.stdout.write(f'  {attr_type.name}: {type_unit_count} units, {item_count} item attributes')
