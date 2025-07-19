from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from customer.models import Company

User = get_user_model()

MAIN_ROLES = [
    ("manager_main", "main_manager"),
    ("salesmanager_main", "main_salesmanager"),
    ("service_main", "main_servicepersonel"),
]

DISTRIBUTOR_ROLES = [
    ("manager_distributor", "manager"),
    ("salesmanager_distributor", "salesmanager"),
    ("service_distributor", "servicepersonel"),
]

class Command(BaseCommand):
    help = 'Create fake users for main company and distributor companies.'

    def handle(self, *args, **options):
        main_company = Company.objects.filter(company_type='main').first()
        if main_company:
            for role, username in MAIN_ROLES:
                user, created = User.objects.get_or_create(
                    username=f"{username}",
                    defaults={
                        'role': role,
                        'company': main_company,
                        'is_staff': True,
                        'is_superuser': False,
                    }
                )
                if created:
                    user.set_password('test1234')
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"Created user {user.username} for main company as {role}"))
                else:
                    self.stdout.write(self.style.WARNING(f"User {user.username} already exists."))
        else:
            self.stdout.write(self.style.ERROR("No main company found!"))

        distributors = Company.objects.filter(company_type='distributor')
        for company in distributors:
            for role, username in DISTRIBUTOR_ROLES:
                user, created = User.objects.get_or_create(
                    username=f"{username}_{company.id}",
                    defaults={
                        'role': role,
                        'company': company,
                        'is_staff': True,
                        'is_superuser': False,
                    }
                )
                if created:
                    user.set_password('test1234')
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"Created user {user.username} for distributor {company.name} as {role}"))
                else:
                    self.stdout.write(self.style.WARNING(f"User {user.username} already exists for distributor {company.name}."))
