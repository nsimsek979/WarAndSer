from django.core.management.base import BaseCommand
from customer.models import Company

def populate_company_city():
    for company in Company.objects.all():
        first_address = company.address.first()
        if first_address and first_address.city:
            company.city = first_address.city
            company.save(update_fields=["city"])

class Command(BaseCommand):
    help = "Populate the city field in Company from the first related Address city."

    def handle(self, *args, **options):
        populate_company_city()
        self.stdout.write(self.style.SUCCESS("Company city fields populated from first address."))
