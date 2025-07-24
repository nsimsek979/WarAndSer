#!/usr/bin/env python
import os
import sys
import django

# Django setup
sys.path.append('D:/GarantiVeServis')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gvs.settings')
django.setup()

from warranty_and_services.models import Installation

# Check installations
total = Installation.objects.count()
with_coords = Installation.objects.filter(
    location_latitude__isnull=False, 
    location_longitude__isnull=False
).count()

print(f"Total installations: {total}")
print(f"Installations with coordinates: {with_coords}")

# Show first few installations
installations = Installation.objects.all()[:5]
for inst in installations:
    print(f"ID: {inst.id}, Customer: {inst.customer.name}, Lat: {inst.location_latitude}, Lng: {inst.location_longitude}")

# Add sample coordinates to first installation if no coordinates exist
if with_coords == 0 and total > 0:
    first_inst = Installation.objects.first()
    first_inst.location_latitude = 39.925533  # Ankara
    first_inst.location_longitude = 32.866287
    first_inst.location_address = "Ankara, Türkiye - Test Address"
    first_inst.save()
    print(f"Added coordinates to installation {first_inst.id}")
    
    # Add coordinates to a few more if available
    if total > 1:
        installations = Installation.objects.all()[1:4]
        coords = [
            (41.0082, 28.9784),  # Istanbul
            (38.4237, 27.1428),  # Izmir  
            (36.8969, 30.7133),  # Antalya
        ]
        
        for i, inst in enumerate(installations):
            if i < len(coords):
                inst.location_latitude = coords[i][0]
                inst.location_longitude = coords[i][1]
                inst.location_address = f"Test Address {i+2}"
                inst.save()
                print(f"Added coordinates to installation {inst.id}")
