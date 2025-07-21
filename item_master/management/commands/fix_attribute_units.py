from django.core.management.base import BaseCommand
from item_master.models import AttributeType, AttributeUnit, InventoryItemAttribute
from django.db import transaction


class Command(BaseCommand):
    help = 'Fix existing AttributeUnit records by assigning them to appropriate AttributeType'

    def handle(self, *args, **options):
        self.stdout.write('Fixing AttributeUnit records...')

        # First, let's see what we have
        units_without_type = AttributeUnit.objects.filter(attribute_type__isnull=True)
        self.stdout.write(f'Found {units_without_type.count()} units without attribute_type')

        if units_without_type.count() == 0:
            self.stdout.write(self.style.SUCCESS('All AttributeUnit records already have attribute_type assigned'))
            return

        # Create default attribute types if they don't exist
        default_types = [
            {'name': 'Genel', 'description': 'General attributes'},
            {'name': 'Boyut', 'description': 'Size and dimension attributes'},
            {'name': 'Güç', 'description': 'Power related attributes'},
            {'name': 'Basınç', 'description': 'Pressure related attributes'},
            {'name': 'Hacim', 'description': 'Volume related attributes'},
        ]

        created_types = {}
        for type_data in default_types:
            attr_type, created = AttributeType.objects.get_or_create(
                name=type_data['name'],
                defaults={'description': type_data['description']}
            )
            created_types[type_data['name']] = attr_type
            if created:
                self.stdout.write(f'Created AttributeType: {attr_type.name}')

        # Define mapping for existing units to attribute types
        unit_mappings = {
            # Power related
            'HP': 'Güç',
            'Kilowatt': 'Güç',
            'Kw': 'Güç',
            'hp': 'Güç',
            'kw': 'Güç',
            
            # Pressure related
            'Bar': 'Basınç',
            'PSI': 'Basınç',
            'bar': 'Basınç',
            'psi': 'Basınç',
            
            # Volume related
            'Litre': 'Hacim',
            'lt': 'Hacim',
            'L': 'Hacim',
            'ml': 'Hacim',
            
            # Size related
            'mm': 'Boyut',
            'cm': 'Boyut',
            'm': 'Boyut',
            'Milimetre': 'Boyut',
            'Metre': 'Boyut',
            'Kilogram': 'Boyut',
            'Kg': 'Boyut',
            'gram': 'Boyut',
            'Adet': 'Boyut',
            'Ad': 'Boyut',
        }

        # Fix existing units
        fixed_count = 0
        with transaction.atomic():
            for unit in units_without_type:
                # Try to find appropriate attribute type
                assigned_type = None
                
                # Check unit name first
                for unit_name, type_name in unit_mappings.items():
                    if unit_name.lower() in unit.name.lower() or unit_name.lower() in unit.symbol.lower():
                        assigned_type = created_types[type_name]
                        break
                
                # If no specific mapping found, assign to 'Genel'
                if not assigned_type:
                    assigned_type = created_types['Genel']
                
                # Update the unit
                unit.attribute_type = assigned_type
                unit.save()
                
                fixed_count += 1
                self.stdout.write(f'Assigned "{unit.name}" to "{assigned_type.name}"')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully fixed {fixed_count} AttributeUnit records')
        )

        # Clean up any orphaned InventoryItemAttribute records
        orphaned_attributes = InventoryItemAttribute.objects.filter(unit__attribute_type__isnull=True)
        if orphaned_attributes.exists():
            self.stdout.write(f'Found {orphaned_attributes.count()} orphaned item attributes')
            orphaned_attributes.delete()
            self.stdout.write('Deleted orphaned item attributes')

        # Summary
        self.stdout.write('\nSummary of AttributeTypes and their Units:')
        for attr_type in AttributeType.objects.all():
            unit_count = attr_type.units.count()
            self.stdout.write(f'  {attr_type.name}: {unit_count} units')
            for unit in attr_type.units.all():
                self.stdout.write(f'    - {unit.name} ({unit.symbol})')
