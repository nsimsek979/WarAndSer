from django.core.management.base import BaseCommand
from custom_user.models import CustomUser
from warranty_and_services.models import Installation
from warranty_and_services.utils import get_user_accessible_companies, get_user_accessible_companies_filter
from django.db.models import Q

class Command(BaseCommand):
    help = 'Test data access for servicepersonel_6 user'

    def handle(self, *args, **options):
        # servicepersonel_6 kullanıcısını al
        try:
            user = CustomUser.objects.get(username='servicepersonel_6')
            self.stdout.write(f"=== {user.username} Data Access Test ===")
            self.stdout.write(f"User Company: {user.company.name} (ID: {user.company.id})")
            self.stdout.write(f"Role: {user.role}")
            
            # Erişebileceği şirketler
            accessible_companies = get_user_accessible_companies(user)
            self.stdout.write(f"Accessible Companies: {accessible_companies}")
            
            # Bu şirketlerin isimlerini göster
            from customer.models import Company
            companies = Company.objects.filter(id__in=accessible_companies)
            self.stdout.write("\nAccessible Company Names:")
            for company in companies:
                self.stdout.write(f"  - {company.name} (ID: {company.id})")
            
            # Installation verilerini kontrol et
            self.stdout.write(f"\n=== Installation Data Access ===")
            
            # Filtresiz tüm installationlar
            all_installations = Installation.objects.all()
            self.stdout.write(f"Total Installations in DB: {all_installations.count()}")
            
            # Kullanıcının görmesi gereken installationlar
            installation_filter = get_user_accessible_companies_filter(user, 'installation')
            user_installations = Installation.objects.filter(installation_filter)
            self.stdout.write(f"User Should See: {user_installations.count()} installations")
            
            # Her installationu detaylı göster
            self.stdout.write("\nDetailed Installation List:")
            for installation in user_installations:
                self.stdout.write(f"  - ID: {installation.id}")
                self.stdout.write(f"    Customer: {installation.customer.name}")
                self.stdout.write(f"    Customer Company ID: {installation.customer.id}")
                self.stdout.write(f"    Inventory Item: {installation.inventory_item}")
                self.stdout.write(f"    Setup Date: {installation.setup_date}")
                self.stdout.write("")
            
            # Ayrıca tüm installationları da gösterelim karşılaştırma için
            self.stdout.write("\n=== ALL Installations (for comparison) ===")
            for installation in all_installations:
                self.stdout.write(f"  - ID: {installation.id}")
                self.stdout.write(f"    Customer: {installation.customer.name}")
                self.stdout.write(f"    Customer Company ID: {installation.customer.id}")
                self.stdout.write(f"    Inventory Item: {installation.inventory_item}")
                self.stdout.write("")
                
        except CustomUser.DoesNotExist:
            self.stdout.write("servicepersonel_6 user not found!")
