
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from datetime import timedelta
import json

try:
    from warranty_and_services.models import Installation, WarrantyFollowUp, ServiceFollowUp
    from warranty_and_services.utils import get_user_accessible_companies_filter
    from customer.models import CoreBusiness
except ImportError:
    # In case the models are not available during migration
    Installation = None
    WarrantyFollowUp = None
    ServiceFollowUp = None
    get_user_accessible_companies_filter = None
    CoreBusiness = None

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
    if Installation and WarrantyFollowUp and ServiceFollowUp and get_user_accessible_companies_filter and CoreBusiness:
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

        # Core Business Installation Statistics - Summary only for dashboard
        core_business_summary_stats = Installation.objects.filter(
            installation_filter,
            customer__core_business__isnull=False
        ).values('customer__core_business').distinct().count()
        
        top_business = Installation.objects.filter(
            installation_filter
        ).values(
            'customer__core_business__name'
        ).annotate(
            installation_count=Count('id')
        ).filter(
            customer__core_business__name__isnull=False
        ).order_by('-installation_count').first()
        
        # Core business summary stats for dashboard
        context['core_business_summary'] = {
            'total_businesses': CoreBusiness.objects.count(),
            'businesses_with_installations': core_business_summary_stats,
            'top_business': top_business
        }

    return render(request, 'dashboard/home.html', context)


@login_required(login_url='login')
def core_business_report(request):
    """Detailed Core Business Installation Report with pagination and limited chart data"""
    context = {}

    # Only generate report if models are available
    if Installation and get_user_accessible_companies_filter and CoreBusiness:
        # Get user's accessible companies filter
        installation_filter = get_user_accessible_companies_filter(request.user, 'installation')
        
        # Get date filter parameter
        date_filter = request.GET.get('period', 'all')
        
        # Calculate date range based on filter
        end_date = timezone.now()
        start_date = None
        
        if date_filter == '1month':
            start_date = end_date - timedelta(days=30)
        elif date_filter == '1quarter':
            start_date = end_date - timedelta(days=90)
        elif date_filter == '1year':
            start_date = end_date - timedelta(days=365)
        # 'all' means no date filter
        
        # Build base queryset
        base_queryset = Installation.objects.filter(installation_filter)
        
        # Apply date filter if specified
        if start_date:
            base_queryset = base_queryset.filter(setup_date__gte=start_date)
        
        # Core Business Installation Statistics - Full data for report
        core_business_stats = base_queryset.values(
            'customer__core_business__name'
        ).annotate(
            installation_count=Count('id')
        ).filter(
            customer__core_business__name__isnull=False
        ).order_by('-installation_count')
        
        # Prepare chart data - Top 9 + Others
        chart_businesses = list(core_business_stats[:9])
        others_count = sum(item['installation_count'] for item in core_business_stats[9:])
        
        if others_count > 0:
            chart_businesses.append({
                'customer__core_business__name': 'Others',
                'installation_count': others_count
            })
        
        # Prepare data for charts (limited to top 9 + others)
        core_business_labels = []
        core_business_data = []
        core_business_colors = [
            '#8B5CF6', '#06B6D4', '#10B981', '#F59E0B', '#EF4444',
            '#EC4899', '#84CC16', '#6366F1', '#F97316', '#64748B'
        ]
        
        for i, stat in enumerate(chart_businesses):
            if stat['customer__core_business__name']:
                name = stat['customer__core_business__name']
                core_business_labels.append(name)
                core_business_data.append(stat['installation_count'])
        
        context['core_business_chart_data'] = {
            'labels': json.dumps(core_business_labels),
            'data': json.dumps(core_business_data),
            'colors': json.dumps(core_business_colors[:len(core_business_data)])
        }
        
        # Total core businesses with installations for the selected period
        total_core_businesses_with_installations = base_queryset.filter(
            customer__core_business__isnull=False
        ).values('customer__core_business').distinct().count()
        
        # Detailed stats for report
        context['report_stats'] = {
            'total_businesses': CoreBusiness.objects.count(),
            'businesses_with_installations': total_core_businesses_with_installations,
            'total_installations': base_queryset.count(),
            'businesses_without_installations': CoreBusiness.objects.count() - total_core_businesses_with_installations
        }
        
        # Top 5 businesses for summary table
        context['top_businesses'] = core_business_stats[:5]
        
        # Pagination for all businesses table
        page = request.GET.get('page', 1)
        per_page = 20  # Show 20 items per page
        
        paginator = Paginator(core_business_stats, per_page)
        try:
            paginated_businesses = paginator.page(page)
        except PageNotAnInteger:
            paginated_businesses = paginator.page(1)
        except EmptyPage:
            paginated_businesses = paginator.page(paginator.num_pages)
        
        # Business details for table with pagination
        context['all_businesses'] = paginated_businesses
        
        # Add current filter to context
        context['current_period'] = date_filter
        
        # Period options for the dropdown
        context['period_options'] = [
            {'value': 'all', 'label': 'All Time'},
            {'value': '1year', 'label': 'Last 1 Year'},
            {'value': '1quarter', 'label': 'Last Quarter (3 months)'},
            {'value': '1month', 'label': 'Last Month'},
        ]

    return render(request, 'dashboard/core_business_report.html', context)
