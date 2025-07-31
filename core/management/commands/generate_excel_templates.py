from django.core.management.base import BaseCommand
from django.http import HttpResponse
from import_export import resources
from import_export.formats.base_formats import XLSX
import os
from django.conf import settings

# Import all resources
from item_master.admin import (
    StatusResource, StockTypeResource, BrandResource, CategoryResource, 
    ItemMasterResource, InventoryItemResource, ItemSparePartResource
)
from customer.admin import (
    CountryResource, CityResource, CountyResource, DistrictResource,
    CoreBusinessResource, CompanyResource, ContactPersonResource, 
    AddressResource, WorkingHoursResource
)
from warranty_and_services.admin import (
    BreakdownCategoryResource, BreakdownReasonResource, InstallationResource,
    WarrantyFollowUpResource, ServiceFollowUpResource, MaintenanceRecordResource
)


class Command(BaseCommand):
    help = 'Generate Excel template files for import operations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='excel_templates',
            help='Directory to save template files (default: excel_templates)'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Define all resources with their names
        resources_list = [
            # Item Master Resources
            ('item_master_status', StatusResource),
            ('item_master_stock_types', StockTypeResource),
            ('item_master_brands', BrandResource),
            ('item_master_categories', CategoryResource),
            ('item_master_products', ItemMasterResource),
            ('inventory_items', InventoryItemResource),
            ('item_spare_parts', ItemSparePartResource),
            
            # Customer Resources
            ('customer_countries', CountryResource),
            ('customer_cities', CityResource),
            ('customer_counties', CountyResource),
            ('customer_districts', DistrictResource),
            ('customer_core_business', CoreBusinessResource),
            ('customer_companies', CompanyResource),
            ('customer_contacts', ContactPersonResource),
            ('customer_addresses', AddressResource),
            ('customer_working_hours', WorkingHoursResource),
            
            # Warranty & Services Resources
            ('warranty_breakdown_categories', BreakdownCategoryResource),
            ('warranty_breakdown_reasons', BreakdownReasonResource),
            ('warranty_installations', InstallationResource),
            ('warranty_follow_ups', WarrantyFollowUpResource),
            ('service_follow_ups', ServiceFollowUpResource),
            ('maintenance_records', MaintenanceRecordResource),
        ]

        xlsx_format = XLSX()
        
        for template_name, resource_class in resources_list:
            try:
                # Create resource instance
                resource = resource_class()
                
                # Create empty dataset with headers
                dataset = resource.export()
                
                # Generate filename
                filename = f"{template_name}_template.xlsx"
                filepath = os.path.join(output_dir, filename)
                
                # Export to Excel
                with open(filepath, 'wb') as f:
                    f.write(xlsx_format.export_data(dataset))
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created template: {filename}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to create {template_name}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n📁 All templates saved to: {os.path.abspath(output_dir)}/')
        )
        
        # Create README file with instructions
        readme_content = """# Excel Import Templates

Bu klasördeki Excel dosyaları, Django admin panelinde veri import işlemleri için kullanılabilir.

## Kullanım Talimatları:

1. İstediğiniz template dosyasını açın
2. Dosyadaki sütun başlıklarını değiştirmeyin
3. Verilerinizi ilgili sütunlara girin
4. Dosyayı kaydedin
5. Django admin panelinde ilgili modele gidin
6. "Import" butonuna tıklayın
7. Dosyanızı seçin ve upload edin

## Template Dosyaları:

### Item Master (Ürün Yönetimi)
- item_master_status_template.xlsx - Ürün durumları
- item_master_stock_types_template.xlsx - Stok türleri  
- item_master_brands_template.xlsx - Markalar
- item_master_categories_template.xlsx - Kategoriler
- item_master_products_template.xlsx - Ana ürünler
- inventory_items_template.xlsx - Stok ürünleri
- item_spare_parts_template.xlsx - Yedek parça ilişkileri

### Customer (Müşteri Yönetimi)
- customer_countries_template.xlsx - Ülkeler
- customer_cities_template.xlsx - Şehirler
- customer_counties_template.xlsx - İlçeler
- customer_districts_template.xlsx - Mahalleler
- customer_core_business_template.xlsx - Ana iş kolları
- customer_companies_template.xlsx - Müşteri firmaları
- customer_contacts_template.xlsx - İletişim bilgileri
- customer_addresses_template.xlsx - Adresler
- customer_working_hours_template.xlsx - Çalışma saatleri

### Warranty & Services (Garanti ve Servisler)
- warranty_breakdown_categories_template.xlsx - Arıza kategorileri
- warranty_breakdown_reasons_template.xlsx - Arıza nedenleri
- warranty_installations_template.xlsx - Kurulumlar
- warranty_follow_ups_template.xlsx - Garanti takipleri
- service_follow_ups_template.xlsx - Servis takipleri
- maintenance_records_template.xlsx - Bakım kayıtları

## Önemli Notlar:

- Foreign Key (ilişki) alanları için mevcut kayıtların tam adlarını kullanın
- Tarih formatı: YYYY-MM-DD (örn: 2024-12-31)
- Boolean (doğru/yanlış) alanları için: True/False
- Boş bırakabileceğiniz alanlar template'te belirtilmiştir

## Sorun Giderme:

- Import sırasında hata alırsanız, sütun başlıklarının değişmediğinden emin olun
- Foreign Key hatalarında, referans verdiğiniz kayıtların sistemde mevcut olduğunu kontrol edin
- Tarih formatı hatalarında YYYY-MM-DD formatını kullanın
"""
        
        readme_path = os.path.join(output_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        self.stdout.write(
            self.style.SUCCESS(f'📄 Created README.md with instructions')
        )
