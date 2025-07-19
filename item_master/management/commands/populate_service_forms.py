from django.core.management.base import BaseCommand
from item_master.models import ServiceForm

class Command(BaseCommand):
    help = 'Populates the database with initial service form data'

    def handle(self, *args, **options):
        service_forms_data = [
            'Panel Check',
            'Valve Check', 
            'Electricity Check',
            'Pressure Check',
            'Environment Check'
        ]

        self.stdout.write(self.style.WARNING('Creating service forms...'))
        
        created_count = 0
        existing_count = 0
        
        for service_form_name in service_forms_data:
            service_form, created = ServiceForm.objects.get_or_create(
                name=service_form_name
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {service_form_name}')
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⚠ Already exists: {service_form_name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary:'
                f'\n- Created {created_count} new service forms'
                f'\n- Found {existing_count} existing service forms'
                f'\n- Total service forms: {ServiceForm.objects.count()}'
            )
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully populated service forms!'))
