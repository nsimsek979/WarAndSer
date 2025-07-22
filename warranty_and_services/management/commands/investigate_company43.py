from django.core.management.base import BaseCommand
from custom_user.models import CustomUser
from warranty_and_services.models import Installation
from customer.models import Company

class Command(BaseCommand):
    help = 'Check why Installation #1 (Company 43) is not showing for servicepersonel_6'

    def handle(self, *args, **options):
        self.stdout.write("=== Investigation: Company 43 (Akşamcı AŞ) ===")
        
        # Company 43 detayları
        try:
            company43 = Company.objects.get(id=43)
            self.stdout.write(f"Company 43: {company43.name}")
            self.stdout.write(f"Company Type: {company43.company_type}")
            self.stdout.write(f"Related Company: {company43.related_company}")
            
            # Installation #1 detayları
            installation1 = Installation.objects.get(id=1)
            self.stdout.write(f"\nInstallation #1:")
            self.stdout.write(f"Customer: {installation1.customer.name}")
            self.stdout.write(f"Customer ID: {installation1.customer.id}")
            self.stdout.write(f"Customer == Company 43: {installation1.customer.id == 43}")
            
            # servicepersonel_6 erişebilir şirketler
            user = CustomUser.objects.get(username='servicepersonel_6')
            from warranty_and_services.utils import get_user_accessible_companies
            accessible = get_user_accessible_companies(user)
            self.stdout.write(f"\nservicepersonel_6 accessible companies: {accessible}")
            self.stdout.write(f"43 in accessible: {43 in accessible}")
            
            # Manuel filtre test
            from django.db.models import Q
            manual_filter = Q(customer__id__in=accessible)
            manual_installations = Installation.objects.filter(manual_filter)
            self.stdout.write(f"\nManual filter results: {list(manual_installations.values('id', 'customer__id', 'customer__name'))}")
            
        except Exception as e:
            self.stdout.write(f"Error: {e}")
