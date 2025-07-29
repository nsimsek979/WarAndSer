#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/d/GarantiVeServis')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gvs.settings')
django.setup()

from django.contrib.auth import get_user_model
from dashboard.views import spare_parts_report
from django.test import RequestFactory
from django.utils import timezone

User = get_user_model()

print("Testing spare_parts_report view...")

try:
    # Create a fake request
    factory = RequestFactory()
    request = factory.get('/reports/spare-parts/')
    
    # Get a user (assuming there is at least one user)
    user = User.objects.first()
    if user:
        request.user = user
        print(f"Using user: {user}")
        
        # Call the view function
        response = spare_parts_report(request)
        print("View executed successfully!")
        print(f"Response status: {response.status_code if hasattr(response, 'status_code') else 'N/A'}")
    else:
        print("No users found in database")
        
except Exception as e:
    print(f"Error in view: {e}")
    print(f"Error type: {type(e)}")
    import traceback
    traceback.print_exc()
