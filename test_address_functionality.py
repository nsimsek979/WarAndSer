#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gvs.settings')
django.setup()

from customer.models import Company, Address, City, Country

def test_address_functionality():
    """Test the customer address functionality"""
    
    print("🧪 Testing Customer Address Functionality")
    print("=" * 50)
    
    # Find or create test company
    try:
        company = Company.objects.filter(company_type='enduser').first()
        if not company:
            company = Company.objects.create(
                name="Test Company",
                company_type='enduser'
            )
            print(f"✅ Created test company: {company.name}")
        else:
            print(f"✅ Using existing company: {company.name}")
        
        # Find or create country and city
        country, created = Country.objects.get_or_create(name="Türkiye")
        city = City.objects.filter(name="İstanbul").first()
        if not city:
            city = City.objects.create(name="İstanbul", country=country)
        
        # Create sample addresses
        addresses_data = [
            {
                'name': 'Merkez Ofis',
                'address': 'Atatürk Mahallesi, İş Merkezi No:123 Kat:5',
                'city': city,
                'country': country,
                'zipcode': '34000'
            },
            {
                'name': 'Fabrika',
                'address': 'Sanayi Sitesi 2. Cadde No:45',
                'city': city,
                'country': country,
                'zipcode': '34100'
            },
            {
                'name': 'Depo',
                'address': 'Lojistik Merkezi A Blok',
                'city': city,
                'country': country,
                'zipcode': '34200'
            }
        ]
        
        # Clear existing addresses for clean test
        Address.objects.filter(company=company).delete()
        
        created_addresses = []
        for addr_data in addresses_data:
            address = Address.objects.create(
                company=company,
                **addr_data
            )
            created_addresses.append(address)
            print(f"✅ Created address: {address.name} - {address.address}")
        
        print(f"\n📊 Summary:")
        print(f"   Company: {company.name} (ID: {company.id})")
        print(f"   Addresses created: {len(created_addresses)}")
        
        # Test API URL
        from django.urls import reverse
        try:
            url = reverse('warranty_and_services:api_customer_addresses', kwargs={'customer_id': company.id})
            print(f"   API URL: {url}")
            print(f"✅ URL routing works correctly")
        except Exception as e:
            print(f"❌ URL routing error: {e}")
        
        print(f"\n🔗 Test the API manually:")
        print(f"   GET /warranty-services/api/customers/{company.id}/addresses/")
        
        return company, created_addresses
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, []

if __name__ == "__main__":
    test_address_functionality()
