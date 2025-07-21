
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

try:
    from warranty_and_services.models import Installation, WarrantyFollowUp, ServiceFollowUp
except ImportError:
    # In case the models are not available during migration
    Installation = None
    WarrantyFollowUp = None
    ServiceFollowUp = None

@login_required(login_url='login')
def home(request):
    context = {}
    
    # Only calculate stats if models are available
    if Installation and WarrantyFollowUp and ServiceFollowUp:
        now = timezone.now()
        
        # Basic stats
        context['total_installations'] = Installation.objects.count()
        context['active_warranties'] = WarrantyFollowUp.objects.filter(
            end_of_warranty_date__gt=now
        ).count()
        context['expiring_warranties'] = WarrantyFollowUp.objects.filter(
            end_of_warranty_date__gt=now,
            end_of_warranty_date__lte=now + timedelta(days=30)
        ).count()
        context['overdue_services'] = ServiceFollowUp.objects.filter(
            is_completed=False,
            next_service_date__lte=now
        ).count()
    
    return render(request, 'dashboard/home.html', context)
