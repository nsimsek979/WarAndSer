from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from customer.models import (
    City, County, District,
    CoreBusiness, Country,
    Company, ContactPerson, Address
)
import random
from faker import Faker

fake = Faker('tr_TR')

class Command(BaseCommand):
    help = "Populates the database with sample Turkish address and company data"

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self.create_locations()
                self.create_core_business()
                self.create_sample_companies()
                
            self.stdout.write(self.style.SUCCESS("Successfully populated all sample data!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

    def create_locations(self):
        # Sample Turkish locations data
        TURKISH_LOCATIONS = {
            "İstanbul": {
                "Adalar": ["Burgazada", "Büyükada", "Heybeliada", "Kınalıada", "Sedefadası"],
                "Arnavutköy": ["Adnan Menderes", "Anadolu", "Arnavutköy Merkez", "Atatürk", "Baklalı"],
                "Ataşehir": ["Aşık Veysel", "Atatürk", "Barbaros", "Esatpaşa", "Ferhatpaşa"],
            },
            "Ankara": {
                "Altındağ": ["Aydınlıkevler", "Doğantepe", "Güneşevler", "Hıdırlıktepe", "Karapürçek"],
                "Çankaya": ["100. Yıl", "Ahlatlıbel", "Anıttepe", "Aşağı Dikmen", "Ata"],
                "Keçiören": ["Aktepe", "Atapark", "Ayvalı", "Bağlarbaşı", "Çaldıran"],
            },
            "İzmir": {
                "Balçova": ["Balçova Merkez", "Çetin Emeç", "Fevzi Çakmak", "Korutürk", "Onur"],
                "Bornova": ["Atatürk", "Barbaros", "Beşyol", "Çamdibi", "Erzene"],
                "Buca": ["Adatepe", "Atatürk", "Barış", "Buca Koop", "Cumhuriyet"],
            }
        }

        # Create Turkey country if not exists
      

        for city_name, counties in TURKISH_LOCATIONS.items():
            city, _ = City.objects.get_or_create(name=city_name)
            
            for county_name, districts in counties.items():
                county, _ = County.objects.get_or_create(
                    name=county_name,
                    city=city
                )
                
                for district_name in districts:
                    District.objects.get_or_create(
                        name=district_name,
                        county=county
                    )


    def create_core_business(self):
        FAALIYET_ALANLARI = [
            "Toptan Ticaret",
            "Perakende Ticaret",
            "Gıda Ürünleri ve İçecek İmalatı",
            "Tekstil Ürünleri İmalatı",
            "Giyim Eşyası İmalatı",
            "Deri ve Deri Ürünleri İmalatı",
            "Ağaç ve Mantar Ürünleri İmalatı",
            "Kağıt ve Kağıt Ürünleri İmalatı",
            "Kok Kömürü ve Rafine Edilmiş Petrol Ürünleri İmalatı",
            "Kimyasal Madde ve Ürünler İmalatı",
        ]
        
        for faaliyet in FAALIYET_ALANLARI:
            CoreBusiness.objects.get_or_create(name=faaliyet)

    def create_sample_companies(self):
    # Use company_type string values directly
        ana_firma_type = "main"
        bayi_type = "distributor"
        son_kullanici_type = "enduser"
        
        # Get random core business
        core_businesses = list(CoreBusiness.objects.all())
        
        # Get Turkey country
        turkey = Country.objects.get(name="Turkey")
        
        # Create Ana Firma
        ana_firma = Company.objects.create(
            name="Ana Firma A.Ş.",
            tax_number="1234567890",
            company_type=ana_firma_type,
            core_business=random.choice(core_businesses),
            email="info@anafirma.com",
            telephone="02121234567",
            active=True
        )
        
        # Create address for Ana Firma
        ana_firma_city = City.objects.get(name="İstanbul")
        ana_firma_county = County.objects.get(name="Ataşehir", city=ana_firma_city)
        ana_firma_district = District.objects.get(name="Atatürk", county=ana_firma_county)
        
        Address.objects.create(
            company=ana_firma,
            name="Merkez Adres",
            country=turkey,
            city=ana_firma_city,
            county=ana_firma_county,
            district=ana_firma_district,
            zipcode="34758",
            address="Atatürk Mah. Küçükbakkalköy Cad. No:5 Ataşehir/İstanbul"
        )
        
        # Create contact person for Ana Firma
        ContactPerson.objects.create(
            company=ana_firma,
            full_name="Ahmet Yılmaz",
            title="Genel Müdür",
            email="ahmet.yilmaz@anafirma.com",
            telephone="05321234567"
        )
        
        # Create Bayi and Son Kullanıcı for each city
        for city in City.objects.all():
            # Create 2 Bayi for each city
            for i in range(1, 3):
                bayi_name = f"{city.name} Bayi {i}"
                bayi = Company.objects.create(
                    name=bayi_name,
                    tax_number=f"10000000{i}",
                    related_company=ana_firma,
                    company_type=bayi_type,
                    core_business=random.choice(core_businesses),
                    email=f"info@{slugify(bayi_name)}.com",
                    telephone=f"0212{random.randint(1000000, 9999999)}",
                    active=True
                )
                
                # Create address for Bayi
                counties = County.objects.filter(city=city)
                if counties.exists():
                    county = random.choice(counties)
                    districts = District.objects.filter(county=county)
                    if districts.exists():
                        district = random.choice(districts)
                        
                        Address.objects.create(
                            company=bayi,
                            name="Bayi Adresi",
                            country=turkey,
                            city=city,
                            county=county,
                            district=district,
                            zipcode=f"34{random.randint(100, 999)}",
                            address=f"{district.name} Mah. {fake.street_name()} No:{random.randint(1, 100)} {county.name}/{city.name}"
                        )
                
                # Create contact person for Bayi
                ContactPerson.objects.create(
                    company=bayi,
                    full_name=fake.name(),
                    title="Bayi Müdürü",
                    email=f"{slugify(fake.first_name())}@{slugify(bayi_name)}.com",
                    telephone=f"053{random.randint(10000000, 99999999)}"
                )
                
                # Create 3 Son Kullanıcı for each Bayi
                for j in range(1, 4):
                    son_kullanici_name = f"{bayi_name} Müşteri {j}"
                    son_kullanici = Company.objects.create(
                        name=son_kullanici_name,
                        tax_number=f"20000000{j}",
                        related_company=bayi,
                        company_type=son_kullanici_type,
                        core_business=random.choice(core_businesses),
                        email=f"info@{slugify(son_kullanici_name)}.com",
                        telephone=f"0212{random.randint(1000000, 9999999)}",
                        active=True
                    )
                    
                    # Create 2 addresses for Son Kullanıcı
                    for k in range(1, 3):
                        counties = County.objects.filter(city=city)
                        if counties.exists():
                            county = random.choice(counties)
                            districts = District.objects.filter(county=county)
                            if districts.exists():
                                district = random.choice(districts)
                                
                                Address.objects.create(
                                    company=son_kullanici,
                                    name=f"Adres {k}",
                                    country=turkey,
                                    city=city,
                                    county=county,
                                    district=district,
                                    zipcode=f"34{random.randint(100, 999)}",
                                    address=f"{district.name} Mah. {fake.street_name()} No:{random.randint(1, 100)} {county.name}/{city.name}"
                                )
                    
                    # Create 2 contact persons for Son Kullanıcı
                    for l in range(1, 3):
                        ContactPerson.objects.create(
                            company=son_kullanici,
                            full_name=fake.name(),
                            title=fake.job(),
                            email=f"{slugify(fake.first_name())}@{slugify(son_kullanici_name)}.com",
                            telephone=f"053{random.randint(10000000, 99999999)}"
                        )