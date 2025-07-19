import os
from django.core.management.base import BaseCommand
from django.db import transaction
from customer.models import City, County, District

# Sample data for 5 cities with their counties and districts
TURKISH_LOCATIONS = {
    "İstanbul": {
        "Adalar": ["Burgazada", "Büyükada", "Heybeliada", "Kınalıada", "Sedefadası"],
        "Arnavutköy": ["Adnan Menderes", "Anadolu", "Arnavutköy Merkez", "Atatürk", "Baklalı"],
        "Ataşehir": ["Aşık Veysel", "Atatürk", "Barbaros", "Esatpaşa", "Ferhatpaşa"],
        # Add more counties and districts as needed
    },
    "Ankara": {
        "Altındağ": ["Aydınlıkevler", "Doğantepe", "Güneşevler", "Hıdırlıktepe", "Karapürçek"],
        "Çankaya": ["100. Yıl", "Ahlatlıbel", "Anıttepe", "Aşağı Dikmen", "Ata"],
        "Keçiören": ["Aktepe", "Atapark", "Ayvalı", "Bağlarbaşı", "Çaldıran"],
        # Add more counties and districts as needed
    },
    "İzmir": {
        "Balçova": ["Balçova Merkez", "Çetin Emeç", "Fevzi Çakmak", "Korutürk", "Onur"],
        "Bornova": ["Atatürk", "Barbaros", "Beşyol", "Çamdibi", "Erzene"],
        "Buca": ["Adatepe", "Atatürk", "Barış", "Buca Koop", "Cumhuriyet"],
        # Add more counties and districts as needed
    },
    "Bursa": {
        "Gemlik": ["Adliye", "Ata", "Balıkpazarı", "Cumhuriyet", "Demirsubaşı"],
        "Gürsu": ["Adaköy", "Ağaköy", "Cumalıkızık", "Hasanağa", "İğdir"],
        "İnegöl": ["Akhisar", "Akıncılar", "Alanyurt", "Arapzade", "Babaoğlu"],
        # Add more counties and districts as needed
    },
    "Antalya": {
        "Alanya": ["Cikcilli", "Demirtaş", "Emişbeleni", "Güzelbağ", "İncekum"],
        "Kepez": ["Altınova", "Antalya", "Aydınlıkevler", "Baraj", "Çallı"],
        "Konyaaltı": ["Akdamlar", "Arapsuyu", "Aydınlık", "Doyran", "Gökdere"],
        # Add more counties and districts as needed
    }
}

class Command(BaseCommand):
    help = "Populates Turkish cities, counties, and districts with sample data"

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self.create_locations()
                
            self.stdout.write(self.style.SUCCESS(
                "Successfully populated Turkish locations with sample data! "
                "Note: This contains sample data for 5 cities. "
                "For complete data, please use official sources."
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

    def create_locations(self):
        city_count = 0
        county_count = 0
        district_count = 0
        
        for city_name, counties in TURKISH_LOCATIONS.items():
            # Create City (İl)
            city, created = City.objects.get_or_create(name=city_name)
            if created:
                city_count += 1
            
            for county_name, districts in counties.items():
                # Create County (İlçe)
                county, created = County.objects.get_or_create(
                    name=county_name,
                    city=city
                )
                if created:
                    county_count += 1
                
                for district_name in districts:
                    # Create District (Mahalle)
                    _, created = District.objects.get_or_create(
                        name=district_name,
                        county=county
                    )
                    if created:
                        district_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"Created/updated: {city_count} cities, {county_count} counties, "
            f"{district_count} districts"
        ))