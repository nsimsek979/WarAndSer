from django.core.management.base import BaseCommand
from datetime import date
from warranty_and_services.models import Installation, WarrantyFollowUp, ServiceFollowUp


class Command(BaseCommand):
    help = 'Fix Installation setup_date None values and recalculate warranty/service dates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find installations with None setup_date
        installations_with_none_date = Installation.objects.filter(setup_date__isnull=True)
        
        self.stdout.write(f"Found {installations_with_none_date.count()} installations with None setup_date")
        
        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made")
            for installation in installations_with_none_date:
                self.stdout.write(f"Would update: {installation} - setup_date to today")
            return
        
        # Update installations with None setup_date to today
        updated_count = 0
        for installation in installations_with_none_date:
            installation.setup_date = date.today()
            installation.save()
            updated_count += 1
            self.stdout.write(f"Updated installation {installation.id}: {installation}")
        
        self.stdout.write(f"Updated {updated_count} installations")
        
        # Find and fix warranty followups with None end_of_warranty_date
        warranty_followups_with_none = WarrantyFollowUp.objects.filter(end_of_warranty_date__isnull=True)
        
        self.stdout.write(f"Found {warranty_followups_with_none.count()} warranty followups with None end_of_warranty_date")
        
        updated_warranties = 0
        for warranty in warranty_followups_with_none:
            # Recalculate warranty end date
            warranty.end_of_warranty_date = warranty.calculate_warranty_end_date()
            warranty.save()
            updated_warranties += 1
            self.stdout.write(f"Updated warranty {warranty.id}: {warranty}")
        
        self.stdout.write(f"Updated {updated_warranties} warranty followups")
        
        # Find and fix service followups with None next_service_date
        service_followups_with_none = ServiceFollowUp.objects.filter(next_service_date__isnull=True)
        
        self.stdout.write(f"Found {service_followups_with_none.count()} service followups with None next_service_date")
        
        updated_services = 0
        for service in service_followups_with_none:
            # Recalculate next service date
            service.next_service_date = service.calculate_next_service_date()
            service.save()
            updated_services += 1
            self.stdout.write(f"Updated service {service.id}: {service}")
        
        self.stdout.write(f"Updated {updated_services} service followups")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully fixed {updated_count} installations, '
                f'{updated_warranties} warranties, and {updated_services} services'
            )
        )
