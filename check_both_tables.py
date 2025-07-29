#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/d/GarantiVeServis')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gvs.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute('PRAGMA table_info(warranty_and_services_maintenancesparepart);')
print("MaintenanceSparePart table structure:")
for row in cursor.fetchall():
    print(f"Column: {row[1]}, Type: {row[2]}")

print("\n" + "="*50 + "\n")

cursor.execute('PRAGMA table_info(warranty_and_services_maintenancerecord);')
print("MaintenanceRecord table structure:")
for row in cursor.fetchall():
    print(f"Column: {row[1]}, Type: {row[2]}")
