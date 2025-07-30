import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Create sample Excel templates for import-export operations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default=os.path.join(settings.BASE_DIR, 'templates', 'excel_templates'),
            help='Output directory for Excel templates'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        # ItemMaster template
        itemmaster_data = {
            'shortcode': ['ITM001', 'ITM002', 'ITM003'],
            'name': ['Sample Product 1', 'Sample Product 2', 'Sample Product 3'],
            'description': ['Description 1', 'Description 2', 'Description 3'],
            'category': ['Category 1', 'Category 2', 'Category 1'],
            'status': ['Active', 'Active', 'Inactive'],
            'brand_name': ['Brand A', 'Brand B', 'Brand A'],
            'stock_type': ['Ticari', 'Yedek Parça', 'Ticari']
        }
        
        df = pd.DataFrame(itemmaster_data)
        df.to_excel(os.path.join(output_dir, 'itemmaster_template.xlsx'), index=False)
        self.stdout.write(
            self.style.SUCCESS(f'Created itemmaster_template.xlsx in {output_dir}')
        )
        
        # InventoryItem template
        inventory_data = {
            'item_shortcode': ['ITM001', 'ITM002', 'ITM003'],
            'item_name': ['Sample Product 1', 'Sample Product 2', 'Sample Product 3'],
            'serial_no': ['SN001', 'SN002', 'SN003'],
            'production_date': ['2024-01-15', '2024-02-20', '2024-03-10'],
            'in_used': [True, False, True]
        }
        
        df = pd.DataFrame(inventory_data)
        df.to_excel(os.path.join(output_dir, 'inventory_template.xlsx'), index=False)
        self.stdout.write(
            self.style.SUCCESS(f'Created inventory_template.xlsx in {output_dir}')
        )
        
        # Category template
        category_data = {
            'category_name': ['Electronics', 'Mechanical', 'Electrical', 'Sub Electronics'],
            'parent_category': ['', '', '', 'Electronics'],
            'slug': ['electronics', 'mechanical', 'electrical', 'sub-electronics']
        }
        
        df = pd.DataFrame(category_data)
        df.to_excel(os.path.join(output_dir, 'category_template.xlsx'), index=False)
        self.stdout.write(
            self.style.SUCCESS(f'Created category_template.xlsx in {output_dir}')
        )
        
        # Brand template
        brand_data = {
            'name': ['Siemens', 'ABB', 'Schneider', 'Phoenix Contact']
        }
        
        df = pd.DataFrame(brand_data)
        df.to_excel(os.path.join(output_dir, 'brand_template.xlsx'), index=False)
        self.stdout.write(
            self.style.SUCCESS(f'Created brand_template.xlsx in {output_dir}')
        )
        
        # StockType template
        stocktype_data = {
            'name': ['Ticari', 'Yedek Parça']
        }
        
        df = pd.DataFrame(stocktype_data)
        df.to_excel(os.path.join(output_dir, 'stocktype_template.xlsx'), index=False)
        self.stdout.write(
            self.style.SUCCESS(f'Created stocktype_template.xlsx in {output_dir}')
        )
        
        # Status template
        status_data = {
            'status': ['Active', 'Inactive', 'Discontinued', 'In Development']
        }
        
        df = pd.DataFrame(status_data)
        df.to_excel(os.path.join(output_dir, 'status_template.xlsx'), index=False)
        self.stdout.write(
            self.style.SUCCESS(f'Created status_template.xlsx in {output_dir}')
        )
        
        # ItemSparePart template
        sparepart_data = {
            'main_item_shortcode': ['ITM001', 'ITM001', 'ITM002'],
            'spare_part_shortcode': ['SP001', 'SP002', 'SP003']
        }
        
        df = pd.DataFrame(sparepart_data)
        df.to_excel(os.path.join(output_dir, 'itemsparepart_template.xlsx'), index=False)
        self.stdout.write(
            self.style.SUCCESS(f'Created itemsparepart_template.xlsx in {output_dir}')
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nAll Excel templates created successfully in {output_dir}\n'
                'You can now use these templates to import data via Django admin.'
            )
        )
