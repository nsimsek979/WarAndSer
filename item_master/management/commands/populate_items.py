from django.core.management.base import BaseCommand
from django.core.files import File
import os
import random
from django.conf import settings
from item_master.models import( 
    ItemMaster, Status, StockType, Brand, Category, ItemImage, ItemSparePart, ServiceForm, WarrantyValue
)

class Command(BaseCommand):
    help = 'Populates the database with initial item data'

    def handle(self, *args, **options):
        # Get or create required related objects
        status_kullanimda, _ = Status.objects.get_or_create(status="Kullanımda")
        stock_type_ticari = StockType.objects.get_or_create(name="Ticari")[0]
        stock_type_yedek = StockType.objects.get_or_create(name="Yedek Parça")[0]
        
        brand_ozen, _ = Brand.objects.get_or_create(name="Özen")
        brand_dalgakiran, _ = Brand.objects.get_or_create(name="Dalgakıran")
        
        category_vidali, _ = Category.objects.get_or_create(category_name="Vidalı Kompresör")
        category_tek_kademeli, _ = Category.objects.get_or_create(category_name="Tek Kademeli Pistonlu")
        category_cift_kademeli, _ = Category.objects.get_or_create(category_name="Çift Kademeli Pistonlu")
        category_hava_filtresi, _ = Category.objects.get_or_create(category_name="Hava Filtresi")
        category_yag_filtresi, _ = Category.objects.get_or_create(category_name="Yağ Filtresi")
        category_seperator, _ = Category.objects.get_or_create(category_name="Seperatör Filtresi")


        items_data = [
            {
                'shortcode': 'OSC3',
                'name': 'Tank Üstü Vidalı Kompresör OSC3',
                'category': category_vidali,
                'status': status_kullanimda,
                'stock_type': stock_type_ticari,
                'brand_name': brand_ozen,
                'has_image': True
            },
            {
                'shortcode': 'OSC4',
                'name': 'Tank Üstü Vidalı Kompresör OSC4',
                'category': category_vidali,
                'status': status_kullanimda,
                'stock_type': stock_type_ticari,
                'brand_name': brand_ozen,
                'has_image': True
            },
            {
                'shortcode': 'OSC5',
                'name': 'Tank Üstü Vidalı Kompresör OSC5',
                'category': category_vidali,
                'status': status_kullanimda,
                'stock_type': stock_type_ticari,
                'brand_name': brand_ozen,
                'has_image': True
            },
            {
                'shortcode': 'OSC7',
                'name': 'Tank Üstü Vidalı Kompresör OSC7',
                'category': category_vidali,
                'status': status_kullanimda,
                'stock_type': stock_type_ticari,
                'brand_name': brand_ozen,
                'has_image': True
            },
            {
                'shortcode': 'OSC11',
                'name': 'Tank Üstü Vidalı Kompresör OSC11',
                'category': category_vidali,
                'status': status_kullanimda,
                'stock_type': stock_type_ticari,
                'brand_name': brand_ozen,
                'has_image': True
            },
            {
                'shortcode': 'TK-100',
                'name': 'TK Modeli Tek Kademeli Pistonlu Hava Kompresörleri TK-100',
                'category': category_tek_kademeli,
                'status': status_kullanimda,
                'stock_type': stock_type_ticari,
                'brand_name': brand_ozen,
                'has_image': True
            },
            {
                'shortcode': 'TK-150',
                'name': 'TK Modeli Tek Kademeli Pistonlu Hava Kompresörleri TK-150',
                'category': category_tek_kademeli,
                'status': status_kullanimda,
                'stock_type': stock_type_ticari,
                'brand_name': brand_ozen,
                'has_image': True
            },
            {
                'shortcode': 'TK-200',
                'name': 'TK Modeli Tek Kademeli Pistonlu Hava Kompresörleri TK-200',
                'category': category_tek_kademeli,
                'status': status_kullanimda,
                'stock_type': stock_type_ticari,
                'brand_name': brand_ozen,
                'has_image': True
            },
            {
                'shortcode': 'ÇK-200',
                'name': 'ÇK Modeli Çift Kademeli Pistonlu Hava Kompresörleri ÇK-200',
                'category': category_cift_kademeli,
                'status': status_kullanimda,
                'stock_type': stock_type_ticari,
                'brand_name': brand_ozen,
                'has_image': True
            },
            {
                'shortcode': 'ÇK-300',
                'name': 'ÇK Modeli Çift Kademeli Pistonlu Hava Kompresörleri ÇK-300',
                'category': category_cift_kademeli,
                'status': status_kullanimda,
                'stock_type': stock_type_ticari,
                'brand_name': brand_ozen,
                'has_image': True
            },
            {
                'shortcode': 'ÇK-500',
                'name': 'ÇK Modeli Çift Kademeli Pistonlu Hava Kompresörleri ÇK-500',
                'category': category_cift_kademeli,
                'status': status_kullanimda,
                'stock_type': stock_type_ticari,
                'brand_name': brand_ozen,
                'has_image': True
            },
            {
                'shortcode': 'DVK-15',
                'name': 'DVK 15 HAVA FİLTRESİ',
                'category': category_hava_filtresi,
                'status': status_kullanimda,
                'stock_type': stock_type_yedek,
                'brand_name': brand_dalgakiran,
                'has_image': False
            },
            {
                'shortcode': 'A1000923',
                'name': '11000923 YAĞ FİLTRESİ',
                'category': category_yag_filtresi,
                'status': status_kullanimda,
                'stock_type': stock_type_yedek,
                'brand_name': brand_dalgakiran,
                'has_image': False
            },
            {
                'shortcode': 'DVK60',
                'name': 'DVK 60 SEPERATÖR FİLTRESİ',
                'category': category_seperator,
                'status': status_kullanimda,
                'stock_type': stock_type_yedek,
                'brand_name': brand_dalgakiran,
                'has_image': False
            },
        ]

        ozen_image_path = os.path.join(settings.BASE_DIR, 'static', 'ozen-kompresor-osc-t-serisi.jpg')

        for item_data in items_data:
            # Create the item
            item, created = ItemMaster.objects.get_or_create(
                shortcode=item_data['shortcode'],
                defaults={
                    'name': item_data['name'],
                    'category': item_data['category'],
                    'status': item_data['status'],
                    'brand_name': item_data['brand_name'],
                    'stock_type': item_data['stock_type'],
                }
            )

            # Add image for Özen brand products that should have images
            if item_data['has_image'] and item_data['brand_name'].name == "Özen":
                # Check if the item already has images
                if not item.images.exists():
                    try:
                        # Use proper file path handling
                        image_name = os.path.basename(ozen_image_path)
                        with open(ozen_image_path, 'rb') as f:
                            image_file = File(f, name=image_name)
                            ItemImage.objects.create(
                                item=item,
                                url=image_file
                            )
                        self.stdout.write(self.style.SUCCESS(f'Added image for {item.shortcode}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error adding image for {item.shortcode}: {str(e)}'))
                        continue

            self.stdout.write(self.style.SUCCESS(f'Processed item: {item.shortcode} - {item.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully populated items'))

        # Spare Parts Section - Create relationships
        self.stdout.write(self.style.WARNING('Setting up spare parts relationships...'))
        
        # Get all spare part items (items with stock_type = "Yedek Parça")
        spare_part_items = ItemMaster.objects.filter(stock_type=stock_type_yedek)
        
        # Get all main items (items with stock_type = "Ticari")
        main_items = ItemMaster.objects.filter(stock_type=stock_type_ticari)
        
        self.stdout.write(self.style.SUCCESS(f'Found {spare_part_items.count()} spare part items:'))
        for spare_part in spare_part_items:
            self.stdout.write(f'  - {spare_part.shortcode}: {spare_part.name}')
        
        self.stdout.write(self.style.SUCCESS(f'Found {main_items.count()} main items:'))
        for main_item in main_items:
            self.stdout.write(f'  - {main_item.shortcode}: {main_item.name}')

        # Assign ALL spare parts to ALL commercial items
        self.stdout.write(self.style.WARNING('Assigning all spare parts to all commercial items...'))
        
        relationships_created = 0
        relationships_existed = 0
        
        for main_item in main_items:
            for spare_part in spare_part_items:
                # Create the relationship if it doesn't exist
                relationship, created = ItemSparePart.objects.get_or_create(
                    main_item=main_item,
                    spare_part_item=spare_part
                )
                
                if created:
                    relationships_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {main_item.shortcode} -> {spare_part.shortcode}'
                        )
                    )
                else:
                    relationships_existed += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ {main_item.shortcode} -> {spare_part.shortcode} (already exists)'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary:'
                f'\n- Created {relationships_created} new relationships'
                f'\n- Found {relationships_existed} existing relationships'
                f'\n- Total relationships: {relationships_created + relationships_existed}'
                f'\n- Expected total: {main_items.count()} x {spare_part_items.count()} = {main_items.count() * spare_part_items.count()}'
            )
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully assigned all spare parts to all commercial items!'))

        # Service Forms Section - Assign service forms to commercial items
        self.stdout.write(self.style.WARNING('Assigning service forms to commercial items...'))
        
        # Get all service forms
        service_forms = ServiceForm.objects.all()
        
        if service_forms.exists():
            self.stdout.write(self.style.SUCCESS(f'Found {service_forms.count()} service forms:'))
            for service_form in service_forms:
                self.stdout.write(f'  - {service_form.name}')
            
            service_assignments = 0
            
            # Assign all service forms to all commercial items
            for main_item in main_items:
                current_service_forms = main_item.service_forms.count()
                
                # Add all service forms to the item
                main_item.service_forms.set(service_forms)
                
                new_service_forms = main_item.service_forms.count()
                if new_service_forms > current_service_forms:
                    service_assignments += (new_service_forms - current_service_forms)
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {main_item.shortcode}: assigned {new_service_forms} service forms')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠ {main_item.shortcode}: already has {new_service_forms} service forms')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nService Forms Summary:'
                    f'\n- Total service forms available: {service_forms.count()}'
                    f'\n- Commercial items updated: {main_items.count()}'
                    f'\n- Each item now has: {service_forms.count()} service forms'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('No service forms found. Run "python manage.py populate_service_forms" first.')
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully assigned service forms to all commercial items!'))

        # Warranty Values Section - Randomly assign warranty values to commercial items
        self.stdout.write(self.style.WARNING('Randomly assigning warranty values to commercial items...'))
        
        # Get all warranty values
        warranty_values = WarrantyValue.objects.all()
        
        if warranty_values.exists():
            self.stdout.write(self.style.SUCCESS(f'Found {warranty_values.count()} warranty values:'))
            for warranty_value in warranty_values:
                self.stdout.write(f'  - {warranty_value.warranty_type.type}: {warranty_value.value}')
            
            warranty_assignments = 0
            
            # Randomly assign 1-2 warranty values to each commercial item
            for main_item in main_items:
                current_warranties = main_item.warranties.count()
                
                if current_warranties == 0:
                    # Randomly select 1 or 2 warranty values
                    num_warranties = random.randint(1, 2)
                    selected_warranties = random.sample(list(warranty_values), min(num_warranties, warranty_values.count()))
                    
                    # Add selected warranties to the item
                    main_item.warranties.set(selected_warranties)
                    
                    warranty_assignments += len(selected_warranties)
                    warranty_names = [f"{w.warranty_type.type}: {w.value}" for w in selected_warranties]
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {main_item.shortcode}: assigned {len(selected_warranties)} warranties - {", ".join(warranty_names)}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠ {main_item.shortcode}: already has {current_warranties} warranties')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nWarranty Values Summary:'
                    f'\n- Total warranty values available: {warranty_values.count()}'
                    f'\n- Commercial items processed: {main_items.count()}'
                    f'\n- Total warranty assignments made: {warranty_assignments}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('No warranty values found. Please create warranty values in the admin first.')
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully assigned warranty values to all commercial items!'))
