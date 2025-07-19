from django.core.management.base import BaseCommand
from item_master.models import WarrantyType, WarrantyValue

class Command(BaseCommand):
    help = 'Populates the database with initial warranty data'

    def handle(self, *args, **options):
        # Create warranty types
        warranty_types_data = [
            'Standard Warranty',
            'Extended Warranty'
        ]

        self.stdout.write(self.style.WARNING('Creating warranty types...'))
        
        warranty_types = []
        for warranty_type_name in warranty_types_data:
            warranty_type, created = WarrantyType.objects.get_or_create(
                type=warranty_type_name
            )
            warranty_types.append(warranty_type)
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created warranty type: {warranty_type_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Warranty type already exists: {warranty_type_name}')
                )

        # Create warranty values for each type
        warranty_values_data = [
            # Standard Warranty values (in months)
            {'type': 'Standard Warranty', 'values': [12, 24, 36]},
            # Extended Warranty values (in months) 
            {'type': 'Extended Warranty', 'values': [48, 60, 72]}
        ]

        self.stdout.write(self.style.WARNING('Creating warranty values...'))
        
        created_values = 0
        existing_values = 0
        
        for warranty_data in warranty_values_data:
            try:
                warranty_type = WarrantyType.objects.get(type=warranty_data['type'])
                
                for value in warranty_data['values']:
                    warranty_value, created = WarrantyValue.objects.get_or_create(
                        warranty_type=warranty_type,
                        value=value
                    )
                    
                    if created:
                        created_values += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Created: {warranty_type.type} - {value} months')
                        )
                    else:
                        existing_values += 1
                        self.stdout.write(
                            self.style.WARNING(f'⚠ Already exists: {warranty_type.type} - {value} months')
                        )
                        
            except WarrantyType.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Warranty type not found: {warranty_data["type"]}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nWarranty Summary:'
                f'\n- Warranty types: {WarrantyType.objects.count()}'
                f'\n- Created {created_values} new warranty values'
                f'\n- Found {existing_values} existing warranty values'
                f'\n- Total warranty values: {WarrantyValue.objects.count()}'
            )
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully populated warranty data!'))
