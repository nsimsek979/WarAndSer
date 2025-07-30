
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from datetime import timedelta
import json

try:
    from warranty_and_services.models import Installation, WarrantyFollowUp, ServiceFollowUp, MaintenanceRecord
    from warranty_and_services.utils import get_user_accessible_companies_filter
    from customer.models import CoreBusiness
except ImportError:
    # In case the models are not available during migration
    Installation = None
    WarrantyFollowUp = None
    ServiceFollowUp = None
    MaintenanceRecord = None
    get_user_accessible_companies_filter = None
    CoreBusiness = None

@login_required(login_url='login')
def home(request):
    context = {}

    # Only calculate stats if models are available
    if Installation and WarrantyFollowUp and ServiceFollowUp and MaintenanceRecord and get_user_accessible_companies_filter and CoreBusiness:
        now = timezone.now()

        # Get user's accessible companies filter for different model types
        installation_filter = get_user_accessible_companies_filter(request.user, 'installation')
        warranty_filter = get_user_accessible_companies_filter(request.user, 'warranty')
        service_filter = get_user_accessible_companies_filter(request.user, 'service')

        # Basic stats
        total_installations = Installation.objects.filter(installation_filter).count()
        context['total_installations'] = total_installations

        # Count distinct items with active warranty coverage (not total warranty count)
        # One item can have multiple warranties, but we count each item only once
        active_warranties = WarrantyFollowUp.objects.filter(
            warranty_filter,
            end_of_warranty_date__gt=now
        ).values('installation__inventory_item').distinct().count()
        context['active_warranties'] = active_warranties

        expiring_warranties = WarrantyFollowUp.objects.filter(
            warranty_filter,
            end_of_warranty_date__gt=now,
            end_of_warranty_date__lte=now + timedelta(days=30)
        ).count()
        context['expiring_warranties'] = expiring_warranties

        overdue_services = ServiceFollowUp.objects.filter(
            service_filter,
            is_completed=False,
            next_service_date__lte=now
        ).count()
        context['overdue_services'] = overdue_services

        # Breakdown maintenance statistics
        breakdown_maintenance_count = MaintenanceRecord.objects.filter(
            service_followup__installation__in=Installation.objects.filter(installation_filter),
            maintenance_type='breakdown'
        ).count()
        context['breakdown_maintenance_count'] = breakdown_maintenance_count
        
        # Recent breakdown maintenance (last 30 days)
        recent_breakdowns = MaintenanceRecord.objects.filter(
            service_followup__installation__in=Installation.objects.filter(installation_filter),
            maintenance_type='breakdown',
            maintenance_date__gte=now - timedelta(days=30)
        ).count()
        context['recent_breakdowns'] = recent_breakdowns

        # Spare Parts Usage Statistics
        from warranty_and_services.models import MaintenanceSparePart
        from django.db.models import Sum
        
        # Spare parts statistics
        spare_parts_count = MaintenanceSparePart.objects.filter(
            maintenance_record__service_followup__installation__in=Installation.objects.filter(installation_filter),
            is_used=True
        ).aggregate(Sum('quantity_used'))['quantity_used__sum'] or 0
        context['spare_parts_count'] = spare_parts_count
        
        # Recent spare parts usage (last 30 days)
        recent_spare_parts = MaintenanceSparePart.objects.filter(
            maintenance_record__service_followup__installation__in=Installation.objects.filter(installation_filter),
            is_used=True,
            maintenance_record__service_date__gte=now - timedelta(days=30)
        ).aggregate(Sum('quantity_used'))['quantity_used__sum'] or 0
        context['recent_spare_parts'] = recent_spare_parts
        
        spare_parts_count = MaintenanceSparePart.objects.filter(
            maintenance_record__service_followup__installation__in=Installation.objects.filter(installation_filter),
            is_used=True
        ).aggregate(Sum('quantity_used'))['quantity_used__sum'] or 0
        context['spare_parts_count'] = spare_parts_count
        
        # Recent spare parts usage (last 30 days)
        recent_spare_parts = MaintenanceSparePart.objects.filter(
            maintenance_record__service_followup__installation__in=Installation.objects.filter(installation_filter),
            is_used=True,
            maintenance_record__service_date__gte=now - timedelta(days=30)
        ).aggregate(Sum('quantity_used'))['quantity_used__sum'] or 0
        context['recent_spare_parts'] = recent_spare_parts

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
        
        # Distributor summary stats for dashboard
        from customer.models import Company
        distributor_summary_stats = Installation.objects.filter(
            installation_filter,
            customer__related_company__isnull=False
        ).values('customer__related_company').distinct().count()
        
        top_distributor = Installation.objects.filter(
            installation_filter
        ).values(
            'customer__related_company__name'
        ).annotate(
            installation_count=Count('id')
        ).filter(
            customer__related_company__name__isnull=False
        ).order_by('-installation_count').first()
        
        context['distributor_summary'] = {
            'total_distributors': Company.objects.filter(company_type='distributor').count(),
            'distributors_with_installations': distributor_summary_stats,
            'top_distributor': top_distributor
        }
        
        # Category summary stats for dashboard
        from item_master.models import Category
        category_summary_stats = Installation.objects.filter(
            installation_filter,
            inventory_item__name__category__isnull=False
        ).values('inventory_item__name__category').distinct().count()
        
        top_category = Installation.objects.filter(
            installation_filter
        ).values(
            'inventory_item__name__category__category_name'
        ).annotate(
            installation_count=Count('id')
        ).filter(
            inventory_item__name__category__category_name__isnull=False
        ).order_by('-installation_count').first()
        
        context['category_summary'] = {
            'total_categories': Category.objects.count(),
            'categories_with_installations': category_summary_stats,
            'top_category': top_category
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
        
        # Get filter parameters
        date_filter = request.GET.get('period', 'all')
        core_business_filter = request.GET.get('core_business', 'all')
        chart_type_filter = request.GET.get('chart_type', 'category')  # 'category' or 'item'
        
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
        
        # Apply core business filter if specified
        if core_business_filter != 'all':
            base_queryset = base_queryset.filter(customer__core_business__id=core_business_filter)
        
        # Core Business Installation Statistics - Full data for report
        core_business_stats = base_queryset.values(
            'customer__core_business__name'
        ).annotate(
            installation_count=Count('id')
        ).filter(
            customer__core_business__name__isnull=False
        ).order_by('-installation_count')
        
        # Prepare chart data - Top 9 + Others for Core Business Chart
        chart_businesses = list(core_business_stats[:9])
        others_count = sum(item['installation_count'] for item in core_business_stats[9:])
        
        if others_count > 0:
            chart_businesses.append({
                'customer__core_business__name': 'Others',
                'installation_count': others_count
            })
        
        # Prepare data for Core Business charts (limited to top 9 + others)
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
        
        # Distribution Overview Chart Data (Categories or Items based on filter)
        distribution_queryset = base_queryset
        
        if chart_type_filter == 'category':
            # Category distribution
            distribution_stats = distribution_queryset.values(
                'inventory_item__name__category__category_name'
            ).annotate(
                installation_count=Count('id')
            ).filter(
                inventory_item__name__category__category_name__isnull=False
            ).order_by('-installation_count')
            
            chart_title = 'Installation Distribution by Category'
            field_name = 'inventory_item__name__category__category_name'
        else:
            # Item Master distribution
            distribution_stats = distribution_queryset.values(
                'inventory_item__name__name'
            ).annotate(
                installation_count=Count('id')
            ).filter(
                inventory_item__name__name__isnull=False
            ).order_by('-installation_count')
            
            chart_title = 'Installation Distribution by Item'
            field_name = 'inventory_item__name__name'
        
        # Prepare distribution chart data - Top 19 + Others
        chart_distribution = list(distribution_stats[:19])
        others_distribution_count = sum(item['installation_count'] for item in distribution_stats[19:])
        
        if others_distribution_count > 0:
            chart_distribution.append({
                field_name: 'Others',
                'installation_count': others_distribution_count
            })
        
        # Prepare data for Distribution charts
        distribution_labels = []
        distribution_data = []
        distribution_colors = [
            '#F59E0B', '#10B981', '#8B5CF6', '#06B6D4', '#EF4444',
            '#EC4899', '#84CC16', '#6366F1', '#F97316', '#64748B',
            '#F472B6', '#A3A3A3', '#FB7185', '#34D399', '#FBBF24',
            '#60A5FA', '#A78BFA', '#F87171', '#4ADE80', '#22D3EE'
        ]
        
        for i, stat in enumerate(chart_distribution):
            if stat[field_name]:
                name = stat[field_name]
                distribution_labels.append(name)
                distribution_data.append(stat['installation_count'])
        
        context['distribution_chart_data'] = {
            'labels': json.dumps(distribution_labels),
            'data': json.dumps(distribution_data),
            'colors': json.dumps(distribution_colors[:len(distribution_data)]),
            'title': chart_title
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
        
        # Add current filters to context
        context['current_period'] = date_filter
        context['current_core_business'] = core_business_filter
        context['current_chart_type'] = chart_type_filter
        
        # Filter options
        context['period_options'] = [
            {'value': 'all', 'label': 'All Time'},
            {'value': '1year', 'label': 'Last 1 Year'},
            {'value': '1quarter', 'label': 'Last Quarter (3 months)'},
            {'value': '1month', 'label': 'Last Month'},
        ]
        
        # Core Business options for filter
        core_businesses = CoreBusiness.objects.all().order_by('name')
        context['core_business_options'] = [{'value': 'all', 'label': 'All Core Businesses'}]
        for cb in core_businesses:
            context['core_business_options'].append({
                'value': str(cb.id),
                'label': cb.name
            })
        
        # Chart type options
        context['chart_type_options'] = [
            {'value': 'category', 'label': 'By Category'},
            {'value': 'item', 'label': 'By Item Master'},
        ]

    return render(request, 'dashboard/core_business_report.html', context)


@login_required(login_url='login')
def distributor_report(request):
    """Detailed Distributor Installation Report with pagination and limited chart data"""
    context = {}

    # Only generate report if models are available
    if Installation and get_user_accessible_companies_filter:
        # Get user's accessible companies filter
        installation_filter = get_user_accessible_companies_filter(request.user, 'installation')
        
        # Get filter parameters
        date_filter = request.GET.get('period', 'all')
        distributor_filter = request.GET.get('distributor', 'all')
        chart_type = request.GET.get('chart_type', 'category')
        
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
        
        # Apply distributor filter if specified
        if distributor_filter != 'all':
            base_queryset = base_queryset.filter(customer__related_company__id=distributor_filter)
        
        # Distributor Installation Statistics - Full data for report
        distributor_stats = base_queryset.values(
            'customer__related_company__name'
        ).annotate(
            installation_count=Count('id')
        ).filter(
            customer__related_company__name__isnull=False
        ).order_by('-installation_count')
        
        # Prepare chart data - Top 9 + Others
        chart_distributors = list(distributor_stats[:9])
        others_count = sum(item['installation_count'] for item in distributor_stats[9:])
        
        if others_count > 0:
            chart_distributors.append({
                'customer__related_company__name': 'Others',
                'installation_count': others_count
            })
        
        # Prepare data for charts (limited to top 9 + others)
        distributor_labels = []
        distributor_data = []
        distributor_colors = [
            '#8B5CF6', '#06B6D4', '#10B981', '#F59E0B', '#EF4444',
            '#EC4899', '#84CC16', '#6366F1', '#F97316', '#64748B'
        ]
        
        for i, stat in enumerate(chart_distributors):
            if stat['customer__related_company__name']:
                name = stat['customer__related_company__name']
                distributor_labels.append(name)
                distributor_data.append(stat['installation_count'])
        
        context['distributor_chart_data'] = {
            'labels': json.dumps(distributor_labels),
            'data': json.dumps(distributor_data),
            'colors': json.dumps(distributor_colors[:len(distributor_data)])
        }
        
        # Distribution Statistics - Category vs Item Master
        if chart_type == 'category':
            distribution_stats = base_queryset.values(
                'inventory_item__name__category__category_name'
            ).annotate(
                installation_count=Count('id')
            ).filter(
                inventory_item__name__category__category_name__isnull=False
            ).order_by('-installation_count')
        else:  # item master
            distribution_stats = base_queryset.values(
                'inventory_item__name__name'
            ).annotate(
                installation_count=Count('id')
            ).filter(
                inventory_item__name__name__isnull=False
            ).order_by('-installation_count')
        
        # Prepare distribution chart data - Top 19 + Others
        chart_distributions = list(distribution_stats[:19])
        others_count = sum(item['installation_count'] for item in distribution_stats[19:])
        
        if others_count > 0:
            if chart_type == 'category':
                chart_distributions.append({
                    'inventory_item__name__category__category_name': 'Others',
                    'installation_count': others_count
                })
            else:
                chart_distributions.append({
                    'inventory_item__name__name': 'Others',
                    'installation_count': others_count
                })
        
        # Prepare data for distribution pie chart
        distribution_labels = []
        distribution_data = []
        distribution_colors = [
            '#8B5CF6', '#06B6D4', '#10B981', '#F59E0B', '#EF4444',
            '#EC4899', '#84CC16', '#6366F1', '#F97316', '#64748B',
            '#0EA5E9', '#14B8A6', '#A855F7', '#F97316', '#EF4444',
            '#22C55E', '#3B82F6', '#F59E0B', '#EC4899', '#6B7280'
        ]
        
        for stat in chart_distributions:
            if chart_type == 'category':
                name = stat['inventory_item__name__category__category_name']
            else:
                name = stat['inventory_item__name__name']
            
            if name:
                distribution_labels.append(name)
                distribution_data.append(stat['installation_count'])
        
        context['distribution_chart_data'] = {
            'labels': json.dumps(distribution_labels),
            'data': json.dumps(distribution_data),
            'colors': json.dumps(distribution_colors[:len(distribution_data)])
        }
        
        # Total distributors with installations for the selected period
        total_distributors_with_installations = base_queryset.filter(
            customer__related_company__isnull=False
        ).values('customer__related_company').distinct().count()
        
        # Get total distributor count
        from customer.models import Company
        total_distributors = Company.objects.filter(company_type='distributor').count()
        
        # Detailed stats for report
        context['report_stats'] = {
            'total_distributors': total_distributors,
            'distributors_with_installations': total_distributors_with_installations,
            'total_installations': base_queryset.count(),
            'distributors_without_installations': total_distributors - total_distributors_with_installations
        }
        
        # Top 5 distributors for summary table
        context['top_distributors'] = distributor_stats[:5]
        
        # Pagination for all distributors table
        page = request.GET.get('page', 1)
        per_page = 20  # Show 20 items per page
        
        paginator = Paginator(distributor_stats, per_page)
        try:
            paginated_distributors = paginator.page(page)
        except PageNotAnInteger:
            paginated_distributors = paginator.page(1)
        except EmptyPage:
            paginated_distributors = paginator.page(paginator.num_pages)
        
        # Distributor details for table with pagination
        context['all_distributors'] = paginated_distributors
        
        # Add current filter to context
        context['current_period'] = date_filter
        context['current_distributor'] = distributor_filter
        context['current_chart_type'] = chart_type
        
        # Period options for the dropdown
        context['period_options'] = [
            {'value': 'all', 'label': 'All Time'},
            {'value': '1year', 'label': 'Last 1 Year'},
            {'value': '1quarter', 'label': 'Last Quarter (3 months)'},
            {'value': '1month', 'label': 'Last Month'},
        ]
        
        # Distributor options (companies with type distributor)
        from customer.models import Company
        distributor_companies = Company.objects.filter(company_type='distributor').order_by('name')
        context['distributor_options'] = [{'value': 'all', 'label': 'All Distributors'}]
        context['distributor_options'].extend([
            {'value': str(company.id), 'label': company.name} 
            for company in distributor_companies
        ])
        
        # Chart type options for distribution chart
        context['chart_type_options'] = [
            {'value': 'category', 'label': 'By Category'},
            {'value': 'item', 'label': 'By Item Master'},
        ]

    return render(request, 'dashboard/distributor_report.html', context)


@login_required(login_url='login')
def category_report(request):
    """Detailed Category Installation Report with pagination and limited chart data"""
    context = {}

    # Only generate report if models are available
    if Installation and get_user_accessible_companies_filter:
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
        
        # Category Installation Statistics - Full data for report (Bar Chart)
        category_stats = base_queryset.values(
            'inventory_item__name__category__category_name'
        ).annotate(
            installation_count=Count('id')
        ).filter(
            inventory_item__name__category__category_name__isnull=False
        ).order_by('-installation_count')
        
        # Parent Category Installation Statistics (Pie Chart)
        parent_category_stats = base_queryset.values(
            'inventory_item__name__category__parent__category_name'
        ).annotate(
            installation_count=Count('id')
        ).filter(
            inventory_item__name__category__parent__category_name__isnull=False
        ).order_by('-installation_count')
        
        # Prepare bar chart data - Top 9 + Others for categories
        chart_categories = list(category_stats[:9])
        others_count = sum(item['installation_count'] for item in category_stats[9:])
        
        if others_count > 0:
            chart_categories.append({
                'inventory_item__name__category__category_name': 'Others',
                'installation_count': others_count
            })
        
        # Prepare data for bar charts (categories)
        category_labels = []
        category_data = []
        category_colors = [
            '#8B5CF6', '#06B6D4', '#10B981', '#F59E0B', '#EF4444',
            '#EC4899', '#84CC16', '#6366F1', '#F97316', '#64748B'
        ]
        
        for i, stat in enumerate(chart_categories):
            if stat['inventory_item__name__category__category_name']:
                name = stat['inventory_item__name__category__category_name']
                category_labels.append(name)
                category_data.append(stat['installation_count'])
        
        # Prepare pie chart data - Top 9 + Others for parent categories  
        chart_parent_categories = list(parent_category_stats[:9])
        others_count = sum(item['installation_count'] for item in parent_category_stats[9:])
        
        if others_count > 0:
            chart_parent_categories.append({
                'inventory_item__name__category__parent__category_name': 'Others',
                'installation_count': others_count
            })
        
        parent_category_labels = []
        parent_category_data = []
        parent_category_colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
        ]
        
        for i, stat in enumerate(chart_parent_categories):
            if stat['inventory_item__name__category__parent__category_name']:
                name = stat['inventory_item__name__category__parent__category_name']
                parent_category_labels.append(name)
                parent_category_data.append(stat['installation_count'])
        
        context['category_chart_data'] = {
            'labels': json.dumps(category_labels),
            'data': json.dumps(category_data),
            'colors': json.dumps(category_colors[:len(category_data)])
        }
        
        context['parent_category_chart_data'] = {
            'labels': json.dumps(parent_category_labels),
            'data': json.dumps(parent_category_data),
            'colors': json.dumps(parent_category_colors[:len(parent_category_data)])
        }
        
        # Category-Distributor Cross Analysis
        category_distributor_stats = base_queryset.values(
            'inventory_item__name__category__category_name',
            'customer__related_company__name'
        ).annotate(
            installation_count=Count('id')
        ).filter(
            inventory_item__name__category__category_name__isnull=False,
            customer__related_company__name__isnull=False
        ).order_by('inventory_item__name__category__category_name', '-installation_count')
        
        # Also include installations by main company (when related_company is null but customer exists)
        main_company_stats = base_queryset.values(
            'inventory_item__name__category__category_name',
            'customer__name'
        ).annotate(
            installation_count=Count('id')
        ).filter(
            inventory_item__name__category__category_name__isnull=False,
            customer__related_company__isnull=True,  # Direct customers without distributor
            customer__name__isnull=False
        ).order_by('inventory_item__name__category__category_name', '-installation_count')
        
        # Get total category count
        from item_master.models import Category
        total_categories = Category.objects.count()
        categories_with_installations = base_queryset.filter(
            inventory_item__name__category__isnull=False
        ).values('inventory_item__name__category').distinct().count()
        
        # Detailed stats for report
        context['report_stats'] = {
            'total_categories': total_categories,
            'categories_with_installations': categories_with_installations,
            'total_installations': base_queryset.count(),
            'categories_without_installations': total_categories - categories_with_installations
        }
        
        # Top 5 categories for summary table
        context['top_categories'] = category_stats[:5]
        
        # Top 5 parent categories for summary table
        context['top_parent_categories'] = parent_category_stats[:5]
        
        # Pagination for all categories table
        page = request.GET.get('page', 1)
        per_page = 20  # Show 20 items per page
        
        paginator = Paginator(category_stats, per_page)
        try:
            paginated_categories = paginator.page(page)
        except PageNotAnInteger:
            paginated_categories = paginator.page(1)
        except EmptyPage:
            paginated_categories = paginator.page(paginator.num_pages)
        
        # Category details for table with pagination
        context['all_categories'] = paginated_categories
        
        # Add category and parent category statistics for template
        context['category_statistics'] = category_stats
        context['parent_category_statistics'] = parent_category_stats
        
        # Category-Distributor cross analysis
        context['category_distributor_stats'] = category_distributor_stats
        context['main_company_stats'] = main_company_stats
        
        # Add current filter to context
        context['current_period'] = date_filter
        
        # Period options for the dropdown
        context['period_options'] = [
            {'value': 'all', 'label': 'All Time'},
            {'value': '1year', 'label': 'Last 1 Year'},
            {'value': '1quarter', 'label': 'Last Quarter (3 months)'},
            {'value': '1month', 'label': 'Last Month'},
        ]

    return render(request, 'dashboard/category_report.html', context)


@login_required(login_url='login')
def breakdown_maintenance_report(request):
    """Detailed Breakdown Maintenance Report with filters and pagination"""
    from item_master.models import ItemMaster, Category
    from warranty_and_services.models import BreakdownCategory, BreakdownReason
    
    context = {}

    # Only generate report if models are available
    if Installation and MaintenanceRecord and get_user_accessible_companies_filter:
        # Get user's accessible companies filter
        installation_filter = get_user_accessible_companies_filter(request.user, 'installation')
        
        # Get filter parameters
        breakdown_category_filter = request.GET.get('breakdown_category', '')
        breakdown_reason_filter = request.GET.get('breakdown_reason', '')
        item_category_filter = request.GET.get('item_category', '')
        item_master_filter = request.GET.get('item_master', '')
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
        
        # Build base queryset for breakdown maintenance only
        base_queryset = MaintenanceRecord.objects.filter(
            service_followup__installation__in=Installation.objects.filter(installation_filter),
            maintenance_type='breakdown'
        ).select_related(
            'service_followup__installation',
            'service_followup__installation__customer',
            'service_followup__installation__inventory_item',
            'service_followup__installation__inventory_item__name',
            'service_followup__installation__inventory_item__name__category',
            'category',
            'breakdown_reason_selected'
        )
        
        # Apply date filter if specified
        if start_date:
            base_queryset = base_queryset.filter(service_date__gte=start_date)
            
        # Apply breakdown category filter
        if breakdown_category_filter:
            base_queryset = base_queryset.filter(category__id=breakdown_category_filter)
            
        # Apply breakdown reason filter
        if breakdown_reason_filter:
            base_queryset = base_queryset.filter(breakdown_reason_selected__id=breakdown_reason_filter)
            
        # Apply item category filter
        if item_category_filter:
            base_queryset = base_queryset.filter(
                service_followup__installation__inventory_item__name__category__id=item_category_filter
            )
            
        # Apply item master filter
        if item_master_filter:
            base_queryset = base_queryset.filter(
                service_followup__installation__inventory_item__name__id=item_master_filter
            )
        
        # Breakdown by Customer/Company
        customer_breakdown_stats = base_queryset.values(
            'service_followup__installation__customer__name'
        ).annotate(
            breakdown_count=Count('id')
        ).order_by('-breakdown_count')
        
        # Breakdown by Breakdown Category
        breakdown_category_stats = base_queryset.values(
            'category__name'
        ).annotate(
            breakdown_count=Count('id')
        ).filter(
            category__name__isnull=False
        ).order_by('-breakdown_count')
        
        # Breakdown by Breakdown Reason
        breakdown_reason_stats = base_queryset.values(
            'breakdown_reason_selected__name'
        ).annotate(
            breakdown_count=Count('id')
        ).filter(
            breakdown_reason_selected__name__isnull=False
        ).order_by('-breakdown_count')
        
        # Breakdown by Category
        category_breakdown_stats = base_queryset.values(
            'service_followup__installation__inventory_item__name__category__category_name'
        ).annotate(
            breakdown_count=Count('id')
        ).filter(
            service_followup__installation__inventory_item__name__category__category_name__isnull=False
        ).order_by('-breakdown_count')
        
        # Monthly breakdown trend - SQLite compatible
        monthly_breakdown_stats = base_queryset.extra(
            select={'month': "strftime('%%Y-%%m', service_date)"}
        ).values('month').annotate(
            breakdown_count=Count('id')
        ).order_by('month')
        
        # Prepare chart data for customer breakdowns - Top 9 + Others
        chart_customers = list(customer_breakdown_stats[:9])
        others_count = sum(item['breakdown_count'] for item in customer_breakdown_stats[9:])
        
        if others_count > 0:
            chart_customers.append({
                'service_followup__installation__customer__name': 'Others',
                'breakdown_count': others_count
            })
        
        # Customer breakdown chart data
        customer_labels = []
        customer_data = []
        customer_colors = [
            '#DC2626', '#EF4444', '#F87171', '#FCA5A5', '#FECACA',
            '#FEE2E2', '#B91C1C', '#991B1B', '#7F1D1D', '#64748B'
        ]
        
        # Prepare chart data for breakdown category breakdowns - All data
        chart_breakdown_categories = list(breakdown_category_stats)
        
        # Breakdown Category chart data
        breakdown_category_labels = []
        breakdown_category_data = []
        breakdown_category_colors = [
            '#DC2626', '#F97316', '#EAB308', '#22C55E', '#06B6D4'
        ]
        
        for stat in chart_breakdown_categories:
            if stat['category__name']:
                breakdown_category_labels.append(stat['category__name'])
                breakdown_category_data.append(stat['breakdown_count'])
        
        # Prepare chart data for breakdown reason breakdowns - Top 9 + Others
        chart_breakdown_reasons = list(breakdown_reason_stats[:9])
        reason_others_count = sum(item['breakdown_count'] for item in breakdown_reason_stats[9:])
        
        if reason_others_count > 0:
            chart_breakdown_reasons.append({
                'breakdown_reason_selected__name': 'Others',
                'breakdown_count': reason_others_count
            })
        
        # Breakdown Reason chart data
        breakdown_reason_labels = []
        breakdown_reason_data = []
        breakdown_reason_colors = [
            '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#3B82F6',
            '#EF4444', '#84CC16', '#F97316', '#06B6D4', '#64748B'
        ]
        
        for stat in chart_breakdown_reasons:
            if stat['breakdown_reason_selected__name']:
                breakdown_reason_labels.append(stat['breakdown_reason_selected__name'])
                breakdown_reason_data.append(stat['breakdown_count'])
        
        # Prepare chart data for category breakdowns - Top 9 + Others
        chart_categories = list(category_breakdown_stats[:9])
        category_others_count = sum(item['breakdown_count'] for item in category_breakdown_stats[9:])
        
        if category_others_count > 0:
            chart_categories.append({
                'service_followup__installation__inventory_item__name__category__category_name': 'Others',
                'breakdown_count': category_others_count
            })
        
        # Category breakdown chart data
        category_labels = []
        category_data = []
        category_colors = [
            '#EF4444', '#F97316', '#EAB308', '#22C55E', '#06B6D4',
            '#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#64748B'
        ]
        
        for stat in chart_categories:
            if stat['service_followup__installation__inventory_item__name__category__category_name']:
                category_labels.append(stat['service_followup__installation__inventory_item__name__category__category_name'])
                category_data.append(stat['breakdown_count'])
        
        # Monthly trend chart data
        monthly_labels = []
        monthly_data = []
        
        for stat in monthly_breakdown_stats:
            if stat['month']:
                monthly_labels.append(stat['month'])
                monthly_data.append(stat['breakdown_count'])
        
        for stat in chart_customers:
            if stat['service_followup__installation__customer__name']:
                customer_labels.append(stat['service_followup__installation__customer__name'])
                customer_data.append(stat['breakdown_count'])
        
        # Prepare comprehensive chart data for all visualizations
        chart_data = {
            'breakdown_category_data': {
                'labels': breakdown_category_labels,
                'data': breakdown_category_data,
                'colors': breakdown_category_colors[:len(breakdown_category_data)]
            },
            'breakdown_reason_data': {
                'labels': breakdown_reason_labels,
                'data': breakdown_reason_data,
                'colors': breakdown_reason_colors[:len(breakdown_reason_data)]
            },
            'customer_data': {
                'labels': customer_labels,
                'data': customer_data,
                'colors': customer_colors[:len(customer_data)]
            },
            'monthly_data': {
                'labels': monthly_labels,
                'data': monthly_data,
                'colors': ['#f97316'] * len(monthly_data)
            },
            'category_data': {
                'labels': category_labels,
                'data': category_data,
                'colors': category_colors[:len(category_data)]
            }
        }
        context['chart_data_json'] = json.dumps(chart_data)
        
        # Summary statistics for dashboard
        total_breakdowns = base_queryset.count()
        customers_affected = customer_breakdown_stats.count()
        # All breakdown records in our query are resolved (since they have MaintenanceRecord)
        avg_resolution_time = 0
        
        # Calculate average resolution time using maintenance_date - service_date
        if base_queryset.exists():
            total_days = 0
            count = 0
            for record in base_queryset:
                if record.service_date and record.maintenance_date:
                    # maintenance_date is already a date object, no need to call .date()
                    maintenance_date = record.maintenance_date
                    days = (maintenance_date - record.service_date).days
                    total_days += days
                    count += 1
            if count > 0:
                avg_resolution_time = total_days / count
        
        context['summary'] = {
            'total_maintenance': total_breakdowns,
            'total_breakdowns': total_breakdowns,
            'customers_affected': customers_affected,
            'avg_resolution_time': avg_resolution_time
        }
        
        # Top customers by breakdown count (renamed for template consistency)
        context['top_customers'] = []
        for customer in customer_breakdown_stats[:5]:
            context['top_customers'].append({
                'customer_name': customer['service_followup__installation__customer__name'],
                'breakdown_count': customer['breakdown_count']
            })
        
        # All maintenance records for main table with additional calculated fields
        all_maintenance_records = base_queryset.order_by('-maintenance_date')
        
        # Add calculated fields for each record
        for record in all_maintenance_records:
            # Calculate resolution days using maintenance_date - service_date
            if record.service_date and record.maintenance_date:
                # maintenance_date is already a date object, no need to call .date()
                maintenance_date = record.maintenance_date
                record.resolution_days = (maintenance_date - record.service_date).days
            else:
                record.resolution_days = None
                
            # Since all records are resolved (they have MaintenanceRecord), no pending cases
            record.days_since_report = None
        
        # Pagination for maintenance records
        page = request.GET.get('page', 1)
        per_page = 20
        
        paginator = Paginator(all_maintenance_records, per_page)
        
        try:
            paginated_records = paginator.page(page)
        except PageNotAnInteger:
            paginated_records = paginator.page(1)
        except EmptyPage:
            paginated_records = paginator.page(paginator.num_pages)
        
        context['maintenance_records'] = paginated_records
        
        # Add current filter to context
        context['current_period'] = date_filter
        
        # Period options for the dropdown
        context['period_options'] = [
            {'value': 'all', 'label': 'All Time'},
            {'value': '1year', 'label': 'Last 1 Year'},
            {'value': '1quarter', 'label': 'Last Quarter (3 months)'},
            {'value': '1month', 'label': 'Last Month'},
        ]
        
        # Add filter options to context
        context['breakdown_categories'] = BreakdownCategory.objects.all()
        context['breakdown_reasons'] = BreakdownReason.objects.all().order_by('name')
        context['item_categories'] = Category.objects.all()
        context['item_masters'] = ItemMaster.objects.all().order_by('name')
        
        # Current filter values
        context['current_breakdown_category'] = breakdown_category_filter
        context['current_breakdown_reason'] = breakdown_reason_filter
        context['current_item_category'] = item_category_filter
        context['current_item_master'] = item_master_filter

    return render(request, 'dashboard/breakdown_maintenance_report.html', context)


def spare_parts_report(request):
    """Detailed Spare Parts Usage Report with filters and pagination"""
    from django.db.models import Sum
    from item_master.models import ItemMaster, Category
    from warranty_and_services.models import MaintenanceSparePart, BreakdownCategory
    
    context = {}

    # Only generate report if models are available
    if Installation and MaintenanceSparePart and get_user_accessible_companies_filter:
        # Get user's accessible companies filter
        installation_filter = get_user_accessible_companies_filter(request.user, 'installation')
        
        # Get filter parameters
        maintenance_type_filter = request.GET.get('maintenance_type', '')
        breakdown_category_filter = request.GET.get('breakdown_category', '')
        item_category_filter = request.GET.get('item_category', '')
        item_master_filter = request.GET.get('item_master', '')
        spare_part_category_filter = request.GET.get('spare_part_category', '')
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
        
        # Build base queryset for spare parts usage
        base_queryset = MaintenanceSparePart.objects.filter(
            maintenance_record__service_followup__installation__in=Installation.objects.filter(installation_filter)
        ).select_related(
            'spare_part',
            'maintenance_record',
            'maintenance_record__service_followup',
            'maintenance_record__service_followup__installation',
            'maintenance_record__service_followup__installation__inventory_item',
            'maintenance_record__service_followup__installation__inventory_item__name',
            'maintenance_record__service_followup__installation__inventory_item__name__category',
            'maintenance_record__category'  # For breakdown category if applicable
        )
        
        # Apply date filter if specified
        if start_date:
            # Use service_date which is the actual date when maintenance was performed
            base_queryset = base_queryset.filter(maintenance_record__service_date__gte=start_date)
            
        # Apply maintenance type filter
        if maintenance_type_filter:
            base_queryset = base_queryset.filter(maintenance_record__maintenance_type=maintenance_type_filter)
            
        # Apply breakdown category filter (only relevant for breakdown maintenance)
        if breakdown_category_filter:
            base_queryset = base_queryset.filter(
                maintenance_record__category__id=breakdown_category_filter,
                maintenance_record__maintenance_type='breakdown'
            )
            
        # Apply item category filter
        if item_category_filter:
            base_queryset = base_queryset.filter(
                maintenance_record__service_followup__installation__inventory_item__name__category__id=item_category_filter
            )
            
        # Apply item master filter
        if item_master_filter:
            base_queryset = base_queryset.filter(
                maintenance_record__service_followup__installation__inventory_item__name__id=item_master_filter
            )
            
        # Apply spare part category filter - if there's no SparePartCategory model, use the ItemMaster category
        if spare_part_category_filter:
            base_queryset = base_queryset.filter(
                spare_part__category__id=spare_part_category_filter
            )
        
        # Summary statistics
        total_spare_parts = base_queryset.aggregate(Sum('quantity_used'))['quantity_used__sum'] or 0
        breakdown_spare_parts = base_queryset.filter(maintenance_record__maintenance_type='breakdown').aggregate(Sum('quantity_used'))['quantity_used__sum'] or 0
        periodic_spare_parts = base_queryset.filter(maintenance_record__maintenance_type='periodic').aggregate(Sum('quantity_used'))['quantity_used__sum'] or 0
        other_spare_parts = base_queryset.filter(maintenance_record__maintenance_type='other').aggregate(Sum('quantity_used'))['quantity_used__sum'] or 0
        
        context['summary'] = {
            'total_spare_parts': total_spare_parts,
            'breakdown_spare_parts': breakdown_spare_parts,
            'periodic_spare_parts': periodic_spare_parts,
            'other_spare_parts': other_spare_parts
        }
        
        # Spare Parts by Category
        spare_part_category_stats = base_queryset.values(
            'spare_part__category__category_name'
        ).annotate(
            parts_count=Sum('quantity_used')
        ).filter(
            spare_part__category__category_name__isnull=False
        ).order_by('-parts_count')
        
        # Spare Parts by Maintenance Type
        maintenance_type_stats = base_queryset.values(
            'maintenance_record__maintenance_type'
        ).annotate(
            parts_count=Sum('quantity_used')
        ).order_by('-parts_count')
        
        # Monthly usage trend - PostgreSQL/SQLite compatible using Django ORM
        from django.db.models.functions import TruncMonth
        
        monthly_usage_stats = base_queryset.annotate(
            month=TruncMonth('maintenance_record__service_date')
        ).values('month').annotate(
            total_parts=Sum('quantity_used')
        ).order_by('month')
        
        # Also get breakdown and periodic parts by month for the chart
        monthly_breakdown_stats = base_queryset.filter(
            maintenance_record__maintenance_type='breakdown'
        ).annotate(
            month=TruncMonth('maintenance_record__service_date')
        ).values('month').annotate(
            parts_count=Sum('quantity_used')
        ).order_by('month')
        
        monthly_periodic_stats = base_queryset.filter(
            maintenance_record__maintenance_type='periodic'
        ).annotate(
            month=TruncMonth('maintenance_record__service_date')
        ).values('month').annotate(
            parts_count=Sum('quantity_used')
        ).order_by('month')
        
        # Top 5 most used spare parts
        top_spare_parts = base_queryset.values(
            'spare_part__name',
            'spare_part__shortcode',
            'spare_part__category__category_name'
        ).annotate(
            count=Sum('quantity_used')
        ).order_by('-count')[:5]
        
        context['top_spare_parts'] = []
        for part in top_spare_parts:
            context['top_spare_parts'].append({
                'name': part['spare_part__name'],
                'part_number': part['spare_part__shortcode'],  # Using shortcode instead of part_number
                'category': part['spare_part__category__category_name'],
                'count': part['count']
            })
        
        # Prepare chart data for spare part categories
        spare_part_category_labels = []
        spare_part_category_data = []
        spare_part_category_colors = [
            '#EF4444', '#F97316', '#EAB308', '#22C55E', '#06B6D4',
            '#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#64748B'
        ]
        
        for stat in spare_part_category_stats:
            if stat['spare_part__category__category_name']:
                spare_part_category_labels.append(stat['spare_part__category__category_name'])
                spare_part_category_data.append(stat['parts_count'])
        
        # Prepare chart data for maintenance types
        maintenance_type_labels = []
        maintenance_type_data = []
        maintenance_type_colors = ['#EF4444', '#3B82F6', '#22C55E']
        maintenance_type_map = {
            'breakdown': 'Breakdown',
            'periodic': 'Periodic',
            'other': 'Other'
        }
        
        for stat in maintenance_type_stats:
            if stat['maintenance_record__maintenance_type'] in maintenance_type_map:
                maintenance_type_labels.append(maintenance_type_map[stat['maintenance_record__maintenance_type']])
                maintenance_type_data.append(stat['parts_count'])
        
        # Monthly trend chart data
        monthly_labels = []
        monthly_total_data = []
        monthly_breakdown_data = []
        monthly_periodic_data = []
        
        # Create a dictionary to efficiently look up values by month
        breakdown_by_month = {stat['month'].strftime('%Y-%m') if stat['month'] else None: stat['parts_count'] for stat in monthly_breakdown_stats}
        periodic_by_month = {stat['month'].strftime('%Y-%m') if stat['month'] else None: stat['parts_count'] for stat in monthly_periodic_stats}
        
        for stat in monthly_usage_stats:
            if stat['month']:
                month_str = stat['month'].strftime('%Y-%m') 
                monthly_labels.append(month_str)
                monthly_total_data.append(stat['total_parts'])
                monthly_breakdown_data.append(breakdown_by_month.get(month_str, 0))
                monthly_periodic_data.append(periodic_by_month.get(month_str, 0))
        
        # Prepare comprehensive chart data for all visualizations
        chart_data = {
            'spare_part_category_data': {
                'labels': spare_part_category_labels,
                'data': spare_part_category_data,
                'colors': spare_part_category_colors[:len(spare_part_category_data)]
            },
            'maintenance_type_data': {
                'labels': maintenance_type_labels,
                'data': maintenance_type_data,
                'colors': maintenance_type_colors[:len(maintenance_type_data)]
            },
            'monthly_data': {
                'labels': monthly_labels,
                'total_data': monthly_total_data,
                'breakdown_data': monthly_breakdown_data,
                'periodic_data': monthly_periodic_data
            }
        }
        context['chart_data_json'] = json.dumps(chart_data)
        
        # All spare parts records for main table
        all_spare_parts_records = base_queryset.order_by('-maintenance_record__service_date')
        
        # Pagination for spare parts records
        page = request.GET.get('page', 1)
        per_page = 20
        
        paginator = Paginator(all_spare_parts_records, per_page)
        
        try:
            paginated_records = paginator.page(page)
        except PageNotAnInteger:
            paginated_records = paginator.page(1)
        except EmptyPage:
            paginated_records = paginator.page(paginator.num_pages)
        
        context['spare_parts_records'] = paginated_records
        
        # Add current filter to context
        context['current_period'] = date_filter
        
        # Period options for the dropdown
        context['period_options'] = [
            {'value': 'all', 'label': 'All Time'},
            {'value': '1year', 'label': 'Last 1 Year'},
            {'value': '1quarter', 'label': 'Last Quarter (3 months)'},
            {'value': '1month', 'label': 'Last Month'},
        ]
        
        # Maintenance type options
        context['maintenance_types'] = [
            {'value': 'breakdown', 'label': 'Breakdown'},
            {'value': 'periodic', 'label': 'Periodic'},
            {'value': 'other', 'label': 'Other'},
        ]
        
        # Add filter options to context
        from warranty_and_services.models import BreakdownCategory
        context['breakdown_categories'] = BreakdownCategory.objects.all()
        context['item_categories'] = Category.objects.all()
        
        # Filter Item Masters by stock_type = "Ticari" 
        context['item_masters'] = ItemMaster.objects.filter(
            stock_type__name="Ticari"
        ).order_by('name')
        
        # Filter Spare Part Categories by stock_type = "Yedek Parça"
        # Get categories that have items with stock_type = "Yedek Parça"
        context['spare_part_categories'] = Category.objects.filter(
            items__stock_type__name="Yedek Parça"
        ).distinct().order_by('category_name')
        
        # Current filter values
        context['current_maintenance_type'] = maintenance_type_filter
        context['current_breakdown_category'] = breakdown_category_filter
        context['current_item_category'] = item_category_filter
        context['current_item_master'] = item_master_filter
        context['current_spare_part_category'] = spare_part_category_filter

    return render(request, 'dashboard/spare_parts_report.html', context)
