
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

try:
    from warranty_and_services.models import Installation, WarrantyFollowUp, ServiceFollowUp
    from warranty_and_services.utils import get_user_accessible_companies_filter
except ImportError:
    # In case the models are not available during migration
    Installation = None
    WarrantyFollowUp = None
    ServiceFollowUp = None
    get_user_accessible_companies_filter = None

@login_required(login_url='login')
def home(request):
    context = {}

    # ...existing code...
    print(f"Debug Dashboard: User {request.user.username}")
    if hasattr(request.user, 'company'):
        print(f"Debug Dashboard: User company: {request.user.company}")
    else:
        print("Debug Dashboard: User has no company attribute")

    # Only calculate stats if models are available
    if Installation and WarrantyFollowUp and ServiceFollowUp and get_user_accessible_companies_filter:
        now = timezone.now()

        # Get user's accessible companies filter for different model types
        installation_filter = get_user_accessible_companies_filter(request.user, 'installation')
        warranty_filter = get_user_accessible_companies_filter(request.user, 'warranty')
        service_filter = get_user_accessible_companies_filter(request.user, 'service')

        print(f"Debug Dashboard: Installation filter: {installation_filter}")

        # Basic stats
        total_installations = Installation.objects.filter(installation_filter).count()
        context['total_installations'] = total_installations
        print(f"Debug Dashboard: Total installations: {total_installations}")

        # Count distinct items with active warranty coverage (not total warranty count)
        # One item can have multiple warranties, but we count each item only once
        active_warranties = WarrantyFollowUp.objects.filter(
            warranty_filter,
            end_of_warranty_date__gt=now
        ).values('installation__inventory_item').distinct().count()
        context['active_warranties'] = active_warranties
        print(f"Debug Dashboard: Active warranties: {active_warranties}")

        expiring_warranties = WarrantyFollowUp.objects.filter(
            warranty_filter,
            end_of_warranty_date__gt=now,
            end_of_warranty_date__lte=now + timedelta(days=30)
        ).count()
        context['expiring_warranties'] = expiring_warranties
        print(f"Debug Dashboard: Expiring warranties: {expiring_warranties}")

        overdue_services = ServiceFollowUp.objects.filter(
            service_filter,
            is_completed=False,
            next_service_date__lte=now
        ).count()
        context['overdue_services'] = overdue_services
        print(f"Debug Dashboard: Overdue services: {overdue_services}")

    return render(request, 'dashboard/home.html', context)
