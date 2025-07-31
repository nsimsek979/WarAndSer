import json
import os
from django.core.management.base import BaseCommand
from customer.models import Country, City, County, District

class Command(BaseCommand):
    help = "Load Turkish cities, counties, and districts from turkey_locations.json"

    def handle(self, *args, **kwargs):
        # Dosya yolu: komut dosyasıyla aynı klasörde
        file_path = os.path.join(os.path.dirname(__file__), "turkey_locations.json")

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR("JSON dosyası bulunamadı."))
            return

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        country, _ = Country.objects.get_or_create(name="Türkiye")

        for city_data in data:
            city_name = city_data["city"]
            city, _ = City.objects.get_or_create(name=city_name, country=country)

            for county_data in city_data["counties"]:
                county_name = county_data["county"]
                county, _ = County.objects.get_or_create(name=county_name, city=city)

                for district_name in county_data["districts"]:
                    District.objects.get_or_create(name=district_name, county=county)

        self.stdout.write(self.style.SUCCESS("Türkiye lokasyon verileri başarıyla yüklendi."))
