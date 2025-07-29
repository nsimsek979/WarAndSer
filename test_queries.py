#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/d/GarantiVeServis')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gvs.settings')
django.setup()

from warranty_and_services.models import MaintenanceSparePart, MaintenanceRecord

print("Testing MaintenanceSparePart queries...")

try:
    # Test basic query
    count = MaintenanceSparePart.objects.count()
    print(f"Total MaintenanceSparePart records: {count}")
    
    # Test query with maintenance_record relationship
    count2 = MaintenanceSparePart.objects.filter(maintenance_record__isnull=False).count()
    print(f"MaintenanceSparePart with maintenance_record: {count2}")
    
    # Test query with service_date filter
    from django.utils import timezone
    from datetime import timedelta
    
    now = timezone.now()
    start_date = now - timedelta(days=30)
    
    count3 = MaintenanceSparePart.objects.filter(
        maintenance_record__service_date__gte=start_date
    ).count()
    print(f"MaintenanceSparePart with service_date >= 30 days ago: {count3}")
    
    print("All queries successful!")
    
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")
