from django.core.management.base import BaseCommand
from django.utils.text import slugify
from item_master.models import Category


class Command(BaseCommand):
    help = 'Create categories from predefined list'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories before creating new ones',
        )

    def handle(self, *args, **options):
        categories_data = {
            "categories": [
                {
                    "name": "Vidalı Hava Kompresörleri",
                    "children": [
                        "OSC T Serisi",
                        "OSC, OSC V Serisi",
                        "OSC U, OSC D Serisi",
                        "OSC DS Serisi"
                    ]
                },
                {
                    "name": "Booster Hava Kompresörleri",
                    "children": [
                        "OBS D Serisi"
                    ]
                },
                {
                    "name": "Pistonlu Hava Kompresörleri",
                    "children": [
                        "Tek Kademeli Kompresörler",
                        "Çift Kademeli Kompresörler"
                    ]
                },
                {
                    "name": "Silobas Hava Kompresörleri",
                    "children": [
                        "Eskintili Silobaslar",
                        "Dizel Silobaslar"
                    ]
                },
                {
                    "name": "Basınçlı Hava Sistemleri",
                    "children": [
                        "Soğutmalı Tip Kurutuocular",
                        "Kimyasal Tip Kurutuocular",
                        "Basınçlı Hava Ekipmanları",
                        "Azot Jeneratörü"
                    ]
                },
                {
                    "name": "Seyyar Kompresör",
                    "children": [
                        "OPC Serisi"
                    ]
                },
                {
                    "name": "Endüstriyel Soğutma Sistemleri",
                    "children": [
                        "OCU Chiller Serisi"
                    ]
                }
            ]
        }

        if options['clear']:
            self.stdout.write('Clearing existing categories...')
            Category.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared all categories')
            )

        created_categories = 0
        updated_categories = 0

        for category_data in categories_data['categories']:
            parent_name = category_data['name']
            
            # Create or get parent category
            parent_category, created = Category.objects.get_or_create(
                category_name=parent_name,
                defaults={
                    'slug': slugify(parent_name),
                    'parent': None
                }
            )
            
            if created:
                created_categories += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created parent category: {parent_name}')
                )
            else:
                updated_categories += 1
                self.stdout.write(
                    self.style.WARNING(f'Parent category already exists: {parent_name}')
                )

            # Create child categories
            for child_name in category_data['children']:
                child_category, created = Category.objects.get_or_create(
                    category_name=child_name,
                    defaults={
                        'slug': slugify(child_name),
                        'parent': parent_category
                    }
                )
                
                if created:
                    created_categories += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  Created child category: {child_name}')
                    )
                else:
                    # Update parent if needed
                    if child_category.parent != parent_category:
                        child_category.parent = parent_category
                        child_category.save()
                        updated_categories += 1
                        self.stdout.write(
                            self.style.WARNING(f'  Updated parent for: {child_name}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'  Child category already exists: {child_name}')
                        )

        self.stdout.write('\n')
        self.stdout.write(
            self.style.SUCCESS(
                f'Categories creation completed!\n'
                f'Created: {created_categories}\n'
                f'Updated: {updated_categories}\n'
                f'Total categories in database: {Category.objects.count()}'
            )
        )

        # Display category tree
        self.stdout.write('\n--- Category Tree ---')
        parent_categories = Category.objects.filter(parent=None).order_by('category_name')
        for parent in parent_categories:
            self.stdout.write(f'├── {parent.category_name}')
            children = Category.objects.filter(parent=parent).order_by('category_name')
            for child in children:
                self.stdout.write(f'│   ├── {child.category_name}')
