from django.core.management.base import BaseCommand
from custom_user.models import CustomUser
from customer.models import Company
from warranty_and_services.models import Installation
from warranty_and_services.utils import get_user_accessible_companies


class Command(BaseCommand):
    help = 'Debug company relationships and data access'
    
    def handle(self, *args, **options):
        self.stdout.write("=== Company Relationship Debug ===")
        
        # List all companies
        companies = Company.objects.all()
        self.stdout.write(f"\nTotal companies: {companies.count()}")
        for company in companies:
            self.stdout.write(f"- {company.name} (Type: {company.company_type}, Related: {company.related_company})")
        
        # List all users with companies
        users = CustomUser.objects.filter(company__isnull=False)
        self.stdout.write(f"\nUsers with companies: {users.count()}")
        for user in users:
            self.stdout.write(f"- {user.username} -> {user.company.name} (Role: {user.role})")
            accessible_companies = get_user_accessible_companies(user)
            self.stdout.write(f"  Accessible company IDs: {accessible_companies}")
        
        # List all installations
        installations = Installation.objects.all()
        self.stdout.write(f"\nTotal installations: {installations.count()}")
        for installation in installations:
            self.stdout.write(f"- Installation {installation.id}: {installation.customer.name}")
        
        self.stdout.write("\n=== End Debug ===")
