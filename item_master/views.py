
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from .models import ItemMaster, Category, Brand, StockType, InventoryItem, InventoryItemAttribute, AttributeType, AttributeUnit, AttributeTypeUnit, Status
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

@login_required(login_url='login')
def inventory_item_list(request):
    from django.utils.translation import gettext as _
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get filter parameters
    category_filter = request.GET.get('category', '')
    brand_filter = request.GET.get('brand', '')
    stock_type_filter = request.GET.get('stock_type', '')
    in_used_filter = request.GET.get('in_used', '')
    item_master_filter = request.GET.get('item_master', '')
    
    # Start with all inventory items with related data
    items = InventoryItem.objects.select_related(
        'name', 'name__category', 'name__brand_name', 'name__stock_type', 'created_by'
    ).prefetch_related('attributes', 'attributes__attribute_type', 'attributes__unit').all()
    
    # Apply role-based filtering for distributor and sales manager users
    user = request.user
    if hasattr(user, 'role') and user.role in ['manager_distributor', 'service_distributor']:
        # Distributor users can only see in-use items installed at their sub-companies
        if hasattr(user, 'company') and user.company:
            # Get all companies under this distributor (including the distributor itself)
            from warranty_and_services.utils import get_user_accessible_companies
            accessible_company_ids = get_user_accessible_companies(user)
            
            # Filter items that are in use and installed at accessible companies
            from warranty_and_services.models import Installation
            installed_item_ids = Installation.objects.filter(
                customer_id__in=accessible_company_ids
            ).values_list('inventory_item_id', flat=True)
            
            # Show only items that are installed at accessible companies
            items = items.filter(id__in=installed_item_ids)
        else:
            # If distributor user has no company assigned, show no items
            items = items.none()
    elif hasattr(user, 'role') and user.role == 'sales_manager':
        # Sales Manager can see:
        # 1. All available items (in_used=False)
        # 2. In-use items installed at their accessible companies
        if hasattr(user, 'company') and user.company:
            from warranty_and_services.utils import get_user_accessible_companies
            accessible_company_ids = get_user_accessible_companies(user)
            
            from warranty_and_services.models import Installation
            # Get in-use items installed at accessible companies
            accessible_in_use_item_ids = Installation.objects.filter(
                customer_id__in=accessible_company_ids
            ).values_list('inventory_item_id', flat=True)
            
            # Filter: available items OR in-use items at accessible companies
            items = items.filter(
                Q(in_used=False) |  # All available items
                Q(id__in=accessible_in_use_item_ids)  # In-use items at accessible companies
            )
        else:
            # If sales manager has no company assigned, show only available items
            items = items.filter(in_used=False)
    
    # Apply search filter
    if search_query:
        items = items.filter(
            Q(name__name__icontains=search_query) |
            Q(name__shortcode__icontains=search_query) |
            Q(serial_no__icontains=search_query)
        )
    
    # Apply category filter
    if category_filter:
        items = items.filter(name__category_id=category_filter)
    
    # Apply brand filter
    if brand_filter:
        items = items.filter(name__brand_name_id=brand_filter)
    
    # Apply stock type filter
    if stock_type_filter:
        items = items.filter(name__stock_type_id=stock_type_filter)
    
    # Apply item master filter
    if item_master_filter:
        items = items.filter(name_id=item_master_filter)
    
    # Apply in_used filter
    if in_used_filter:
        if in_used_filter == 'true':
            items = items.filter(in_used=True)
        elif in_used_filter == 'false':
            items = items.filter(in_used=False)
    
    # Order by creation date (newest first)
    items = items.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(items, 15)  # Show 15 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = Category.objects.all().order_by('category_name')
    brands = Brand.objects.all().order_by('name')
    stock_types = StockType.objects.all().order_by('name')
    
    # Get selected item master if filtered
    selected_item_master = None
    if item_master_filter:
        try:
            selected_item_master = ItemMaster.objects.get(id=item_master_filter)
        except ItemMaster.DoesNotExist:
            pass
    
    # Calculate stats based on filtered items (before pagination)
    total_items = items.count()
    in_use_items = items.filter(in_used=True).count()
    available_items = items.filter(in_used=False).count()
    
    # Add low stock calculation (optional)
    low_stock_items = 0  # This would need business logic definition
    
    # Order by creation date (newest first) AFTER stats calculation
    items = items.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(items, 15)  # Show 15 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = Category.objects.all().order_by('category_name')
    brands = Brand.objects.all().order_by('name')
    stock_types = StockType.objects.all().order_by('name')

    context = {
        'items': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'brand_filter': brand_filter,
        'stock_type_filter': stock_type_filter,
        'in_used_filter': in_used_filter,
        'item_master_filter': item_master_filter,
        'selected_item_master': selected_item_master,
        'categories': categories,
        'brands': brands,
        'stock_types': stock_types,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_items': total_items,
        'in_use_items': in_use_items,
        'available_items': available_items,
        'low_stock_items': low_stock_items,
    }
    return render(request, 'pages/inventory/inventory-item-list.html', context)

@login_required(login_url='login')
def inventory_item_detail(request, pk):
    from django.utils.translation import gettext as _
    
    # Get the inventory item with all related data
    item = get_object_or_404(
        InventoryItem.objects.select_related(
            'name', 'name__category', 'name__brand_name', 'name__stock_type', 
            'name__status', 'created_by'
        ).prefetch_related(
            'name__images', 'name__warranties', 'name__service_forms', 'name__specs',
            'name__maintenance_schedules', 'name__maintenance_schedules__service_period_value',
            'name__maintenance_schedules__service_period_value__service_period_type',
            'attributes', 'attributes__attribute_type', 'attributes__unit'
        ), 
        pk=pk
    )
    
    # Check if distributor or sales manager user has access to this item
    user = request.user
    if hasattr(user, 'role') and user.role in ['manager_distributor', 'service_distributor']:
        if hasattr(user, 'company') and user.company:
            from warranty_and_services.utils import get_user_accessible_companies
            accessible_company_ids = get_user_accessible_companies(user)
            
            # Check if this item is installed at any accessible company
            from warranty_and_services.models import Installation
            item_installations = Installation.objects.filter(
                inventory_item=item,
                customer_id__in=accessible_company_ids
            )
            
            if not item_installations.exists():
                # Item is not accessible to this distributor user
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("You don't have permission to access this item.")
        else:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Your company information is not defined.")
    elif hasattr(user, 'role') and user.role == 'sales_manager':
        # Sales manager can access:
        # 1. Available items (in_used=False)
        # 2. In-use items installed at accessible companies
        if item.in_used:  # If item is in use, check if it's at accessible company
            if hasattr(user, 'company') and user.company:
                from warranty_and_services.utils import get_user_accessible_companies
                accessible_company_ids = get_user_accessible_companies(user)
                
                from warranty_and_services.models import Installation
                item_installations = Installation.objects.filter(
                    inventory_item=item,
                    customer_id__in=accessible_company_ids
                )
                
                if not item_installations.exists():
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied("You don't have permission to access this item.")
            else:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("Your company information is not defined.")
        # If item is available (in_used=False), sales manager can always access it
    
    # Get related inventory items for the same ItemMaster
    related_items_queryset = InventoryItem.objects.filter(
        name=item.name
    ).exclude(pk=item.pk).select_related('created_by').order_by('-created_at')
    
    # Apply same filtering logic for related items if user is distributor or sales manager
    if hasattr(user, 'role') and user.role in ['manager_distributor', 'service_distributor']:
        if hasattr(user, 'company') and user.company:
            # Filter related items to only show those installed at accessible companies
            from warranty_and_services.models import Installation
            accessible_related_item_ids = Installation.objects.filter(
                customer_id__in=accessible_company_ids
            ).values_list('inventory_item_id', flat=True).distinct()
            
            related_items = related_items_queryset.filter(id__in=accessible_related_item_ids)[:5]
        else:
            related_items = InventoryItem.objects.none()  # No items if no company
    elif hasattr(user, 'role') and user.role == 'sales_manager':
        if hasattr(user, 'company') and user.company:
            from warranty_and_services.utils import get_user_accessible_companies
            accessible_company_ids = get_user_accessible_companies(user)
            
            # Filter related items: available items OR in-use items at accessible companies
            from warranty_and_services.models import Installation
            accessible_in_use_item_ids = Installation.objects.filter(
                customer_id__in=accessible_company_ids
            ).values_list('inventory_item_id', flat=True).distinct()
            
            related_items = related_items_queryset.filter(
                Q(in_used=False) |  # Available items
                Q(id__in=accessible_in_use_item_ids)  # In-use items at accessible companies
            )[:5]
        else:
            # Show only available items if no company assigned
            related_items = related_items_queryset.filter(in_used=False)[:5]
    else:
        related_items = related_items_queryset[:5]
    
    # Get spare parts for the main item
    from .models import ItemSparePart
    spare_part_relationships = ItemSparePart.objects.filter(
        main_item=item.name
    ).select_related(
        'spare_part_item__category', 
        'spare_part_item__brand_name', 
        'spare_part_item__stock_type'
    )[:5]
    spare_parts_list = [rel.spare_part_item for rel in spare_part_relationships]
    
    context = {
        'item': item,
        'related_items': related_items,
        'spare_parts': spare_parts_list,
    }
    return render(request, 'pages/inventory/inventory-item-detail.html', context)

@login_required(login_url='login')
def item_master_list(request):
    from django.utils.translation import gettext as _
    from django.db.models import Count
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get filter parameters
    category_filter = request.GET.get('category', '')
    brand_filter = request.GET.get('brand', '')
    stock_type_filter = request.GET.get('stock_type', '')
    
    # Start with all items and annotate with inventory item counts
    items = ItemMaster.objects.select_related('category', 'brand_name', 'stock_type', 'status').annotate(
        inventory_count=Count('inventory_items'),
        available_count=Count('inventory_items', filter=Q(inventory_items__in_used=False)),
        in_use_count=Count('inventory_items', filter=Q(inventory_items__in_used=True))
    ).all()
    
    # Apply search filter
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(shortcode__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply category filter
    if category_filter:
        items = items.filter(category_id=category_filter)
    
    # Apply brand filter
    if brand_filter:
        items = items.filter(brand_name_id=brand_filter)
    
    # Apply stock type filter
    if stock_type_filter:
        items = items.filter(stock_type_id=stock_type_filter)
    
    # Order by name
    items = items.order_by('name')
    
    # Pagination
    paginator = Paginator(items, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = Category.objects.all().order_by('category_name')
    brands = Brand.objects.all().order_by('name')
    stock_types = StockType.objects.all().order_by('name')
    
    context = {
        'items': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'brand_filter': brand_filter,
        'stock_type_filter': stock_type_filter,
        'categories': categories,
        'brands': brands,
        'stock_types': stock_types,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, 'pages/itemmaster/item-master-list.html', context)

@login_required(login_url='login')
def item_master_detail(request, pk):
    item = get_object_or_404(
        ItemMaster.objects.select_related(
            'category', 'brand_name', 'stock_type', 'status'
        ).prefetch_related(
            'images', 'warranties', 'service_forms', 'specs',
            'maintenance_schedules__service_period_value__service_period_type'
        ), 
        pk=pk
    )
    
    # Get spare parts where this item is the main item using the through model
    from .models import ItemSparePart
    from django.core.paginator import Paginator
    
    spare_part_relationships = ItemSparePart.objects.filter(
        main_item=item
    ).select_related(
        'spare_part_item__category', 
        'spare_part_item__brand_name', 
        'spare_part_item__stock_type'
    )
    spare_parts_list = [rel.spare_part_item for rel in spare_part_relationships]
    
    # Pagination for spare parts
    spare_parts_paginator = Paginator(spare_parts_list, 5)  # Show 5 spare parts per page
    spare_parts_page = request.GET.get('spare_parts_page')
    spare_parts = spare_parts_paginator.get_page(spare_parts_page)
    
    # Get items that use this item as a spare part
    used_in_relationships = ItemSparePart.objects.filter(
        spare_part_item=item
    ).select_related(
        'main_item__category', 
        'main_item__brand_name', 
        'main_item__stock_type'
    )
    used_in_items_list = [rel.main_item for rel in used_in_relationships]
    
    # Pagination for used in items
    used_in_paginator = Paginator(used_in_items_list, 5)  # Show 5 items per page
    used_in_page = request.GET.get('used_in_page')
    used_in_items = used_in_paginator.get_page(used_in_page)
    
    context = {
        'item': item,
        'spare_parts': spare_parts,
        'used_in_items': used_in_items,
    }
    return render(request, 'pages/itemmaster/item-master-detail.html', context)

@login_required(login_url='login')
@permission_required('item_master.add_itemmaster', raise_exception=True)
def item_master_create(request):
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils.text import slugify
    
    if request.method == 'POST':
        # Get form data
        shortcode = request.POST.get('shortcode', '').strip()
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand_name')
        stock_type_id = request.POST.get('stock_type')
        status_id = request.POST.get('status')
        
        # Basic validation
        errors = []
        if not shortcode:
            errors.append("Shortcode is required")
        elif ItemMaster.objects.filter(shortcode=shortcode).exists():
            errors.append("Shortcode already exists")
            
        if not name:
            errors.append("Name is required")
            
        if not category_id:
            errors.append("Category is required")
            
        if not stock_type_id:
            errors.append("Stock Type is required")
            
        if not status_id:
            errors.append("Status is required")
            
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Create the item
                item = ItemMaster.objects.create(
                    shortcode=shortcode,
                    name=name,
                    description=description if description else None,
                    category_id=category_id if category_id else None,
                    brand_name_id=brand_id if brand_id else None,
                    stock_type_id=stock_type_id,
                    status_id=status_id,
                    slug=slugify(name)
                )
                
                # Handle file uploads
                from .models import ItemImage, ItemSpec, ItemSparePart, ServiceForm, WarrantyValue
                
                # Handle images
                images = request.FILES.getlist('images')
                for image in images:
                    ItemImage.objects.create(item=item, url=image)
                
                # Handle specification files
                specs = request.FILES.getlist('specs')
                for spec in specs:
                    ItemSpec.objects.create(item=item, url=spec)
                
                # Handle spare parts relationships
                spare_part_ids = request.POST.getlist('spare_parts')
                for spare_part_id in spare_part_ids:
                    if spare_part_id:
                        try:
                            spare_part_item = ItemMaster.objects.get(id=spare_part_id)
                            ItemSparePart.objects.create(main_item=item, spare_part_item=spare_part_item)
                        except ItemMaster.DoesNotExist:
                            pass
                
                # Handle service forms
                service_form_ids = request.POST.getlist('service_forms')
                for service_form_id in service_form_ids:
                    if service_form_id:
                        try:
                            service_form = ServiceForm.objects.get(id=service_form_id)
                            item.service_forms.add(service_form)
                        except ServiceForm.DoesNotExist:
                            pass
                
                # Handle warranties
                warranty_ids = request.POST.getlist('warranties')
                for warranty_id in warranty_ids:
                    if warranty_id:
                        try:
                            warranty = WarrantyValue.objects.get(id=warranty_id)
                            item.warranties.add(warranty)
                        except WarrantyValue.DoesNotExist:
                            pass
                
                # Handle maintenance schedules
                from .models import MaintenanceSchedule, ServicePeriodValue
                maintenance_period_ids = request.POST.getlist('maintenance_periods')
                maintenance_descriptions = request.POST.getlist('maintenance_descriptions')
                maintenance_is_critical = request.POST.getlist('maintenance_is_critical')
                
                # Track service period types to prevent duplicates
                added_service_types = set()
                
                for i, period_id in enumerate(maintenance_period_ids):
                    if period_id:
                        try:
                            service_period_value = ServicePeriodValue.objects.get(id=period_id)
                            service_type = service_period_value.service_period_type.type
                            
                            # Check if this service type was already added
                            if service_type in added_service_types:
                                messages.warning(request, f'You can\'t add the same service period type multiple times: {service_type}. Only the first one was added.')
                                continue
                            
                            description = maintenance_descriptions[i] if i < len(maintenance_descriptions) else ''
                            is_critical = str(i) in maintenance_is_critical  # Check if checkbox was checked
                            
                            MaintenanceSchedule.objects.create(
                                item_master=item,
                                service_period_value=service_period_value,
                                is_critical=is_critical,
                                maintenance_description=description
                            )
                            
                            added_service_types.add(service_type)
                            
                        except ServicePeriodValue.DoesNotExist:
                            pass
                
                messages.success(request, f'Item "{item.name}" created successfully!')
                return redirect('item-master:item_master_detail', pk=item.pk)
                
            except Exception as e:
                messages.error(request, f'Error creating item: {str(e)}')
    
    # Get filter options for form
    from .models import Status, WarrantyValue, ServiceForm, ServicePeriodValue
    categories = Category.objects.all().order_by('category_name')
    brands = Brand.objects.all().order_by('name')
    stock_types = StockType.objects.all().order_by('name')
    statuses = Status.objects.all().order_by('status')
    
    # Get existing warranty values, service forms and service periods for selection
    warranty_values = WarrantyValue.objects.select_related('warranty_type').all().order_by('warranty_type__type', 'value')
    service_forms = ServiceForm.objects.all().order_by('name')
    service_period_values = ServicePeriodValue.objects.select_related('service_period_type').all().order_by('service_period_type__type', 'value')
    
    # Get items for spare parts selection (only spare part stock type)
    try:
        spare_part_stock_type = StockType.objects.get(name="Yedek Parça")
        spare_part_items = ItemMaster.objects.filter(stock_type=spare_part_stock_type).order_by('shortcode', 'name')
    except StockType.DoesNotExist:
        spare_part_items = ItemMaster.objects.none()
    
    context = {
        'categories': categories,
        'brands': brands,
        'stock_types': stock_types,
        'statuses': statuses,
        'warranty_values': warranty_values,
        'service_forms': service_forms,
        'service_period_values': service_period_values,
        'spare_part_items': spare_part_items,
    }
    return render(request, 'pages/itemmaster/item-master-create.html', context)

@login_required(login_url='login')
@permission_required('item_master.change_itemmaster', raise_exception=True)
def item_master_update(request, pk):
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils.text import slugify
    
    item = get_object_or_404(ItemMaster, pk=pk)
    
    if request.method == 'POST':
        # Get form data
        shortcode = request.POST.get('shortcode', '').strip()
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand_name')
        stock_type_id = request.POST.get('stock_type')
        status_id = request.POST.get('status')
        
        # Basic validation
        errors = []
        if not shortcode:
            errors.append("Shortcode is required")
        elif ItemMaster.objects.filter(shortcode=shortcode).exclude(pk=item.pk).exists():
            errors.append("Shortcode already exists")
            
        if not name:
            errors.append("Name is required")
            
        if not category_id:
            errors.append("Category is required")
            
        if not stock_type_id:
            errors.append("Stock Type is required")
            
        if not status_id:
            errors.append("Status is required")
            
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Update the item
                item.shortcode = shortcode
                item.name = name
                item.description = description if description else None
                item.category_id = category_id if category_id else None
                item.brand_name_id = brand_id if brand_id else None
                item.stock_type_id = stock_type_id
                item.status_id = status_id
                item.slug = slugify(name)
                item.save()
                
                # Handle file uploads
                from .models import ItemImage, ItemSpec, ItemSparePart, ServiceForm, WarrantyValue
                
                # Handle deleted images
                delete_image_ids = request.POST.getlist('delete_images')
                for image_id in delete_image_ids:
                    if image_id:
                        try:
                            image = ItemImage.objects.get(id=image_id, item=item)
                            # Delete the file from filesystem
                            if image.url:
                                image.url.delete(save=False)
                            image.delete()
                        except ItemImage.DoesNotExist:
                            pass
                
                # Handle deleted specs
                delete_spec_ids = request.POST.getlist('delete_specs')
                for spec_id in delete_spec_ids:
                    if spec_id:
                        try:
                            spec = ItemSpec.objects.get(id=spec_id, item=item)
                            # Delete the file from filesystem
                            if spec.url:
                                spec.url.delete(save=False)
                            spec.delete()
                        except ItemSpec.DoesNotExist:
                            pass
                
                # Handle new images
                images = request.FILES.getlist('images')
                for image in images:
                    ItemImage.objects.create(item=item, url=image)
                
                # Handle new specification files
                specs = request.FILES.getlist('specs')
                for spec in specs:
                    ItemSpec.objects.create(item=item, url=spec)
                
                # Handle spare parts relationships - clear and rebuild
                ItemSparePart.objects.filter(main_item=item).delete()
                spare_part_ids = request.POST.getlist('spare_parts')
                for spare_part_id in spare_part_ids:
                    if spare_part_id:
                        try:
                            spare_part_item = ItemMaster.objects.get(id=spare_part_id)
                            ItemSparePart.objects.create(main_item=item, spare_part_item=spare_part_item)
                        except ItemMaster.DoesNotExist:
                            pass
                
                # Handle service forms - clear and rebuild
                item.service_forms.clear()
                service_form_ids = request.POST.getlist('service_forms')
                for service_form_id in service_form_ids:
                    if service_form_id:
                        try:
                            service_form = ServiceForm.objects.get(id=service_form_id)
                            item.service_forms.add(service_form)
                        except ServiceForm.DoesNotExist:
                            pass
                
                # Handle warranties - clear and rebuild
                item.warranties.clear()
                warranty_ids = request.POST.getlist('warranties')
                for warranty_id in warranty_ids:
                    if warranty_id:
                        try:
                            warranty = WarrantyValue.objects.get(id=warranty_id)
                            item.warranties.add(warranty)
                        except WarrantyValue.DoesNotExist:
                            pass
                
                # Handle maintenance schedules - clear and rebuild
                from .models import MaintenanceSchedule, ServicePeriodValue
                MaintenanceSchedule.objects.filter(item_master=item).delete()
                
                maintenance_period_ids = request.POST.getlist('maintenance_periods')
                maintenance_descriptions = request.POST.getlist('maintenance_descriptions')
                maintenance_is_critical = request.POST.getlist('maintenance_is_critical')
                
                # Track service period types to prevent duplicates
                added_service_types = set()
                
                for i, period_id in enumerate(maintenance_period_ids):
                    if period_id:
                        try:
                            service_period_value = ServicePeriodValue.objects.get(id=period_id)
                            service_type = service_period_value.service_period_type.type
                            
                            # Check if this service type was already added
                            if service_type in added_service_types:
                                messages.warning(request, f'You can\'t add the same service period type multiple times: {service_type}. Only the first one was added.')
                                continue
                            
                            description = maintenance_descriptions[i] if i < len(maintenance_descriptions) else ''
                            is_critical = str(i) in maintenance_is_critical  # Check if checkbox was checked
                            
                            MaintenanceSchedule.objects.create(
                                item_master=item,
                                service_period_value=service_period_value,
                                is_critical=is_critical,
                                maintenance_description=description
                            )
                            
                            added_service_types.add(service_type)
                            
                        except ServicePeriodValue.DoesNotExist:
                            pass
                
                messages.success(request, f'Item "{item.name}" updated successfully!')
                return redirect('item-master:item_master_detail', pk=item.pk)
                
            except Exception as e:
                messages.error(request, f'Error updating item: {str(e)}')
    
    # Get filter options for form
    from .models import Status, WarrantyValue, ServiceForm, ServicePeriodValue
    categories = Category.objects.all().order_by('category_name')
    brands = Brand.objects.all().order_by('name')
    stock_types = StockType.objects.all().order_by('name')
    statuses = Status.objects.all().order_by('status')
    
    # Get existing warranty values, service forms and service periods for selection
    warranty_values = WarrantyValue.objects.select_related('warranty_type').all().order_by('warranty_type__type', 'value')
    service_forms = ServiceForm.objects.all().order_by('name')
    service_period_values = ServicePeriodValue.objects.select_related('service_period_type').all().order_by('service_period_type__type', 'value')
    
    # Get current maintenance schedules for the item
    current_maintenance_schedules = item.maintenance_schedules.all().select_related('service_period_value__service_period_type')
    
    # Get items for spare parts selection (only spare part stock type)
    try:
        spare_part_stock_type = StockType.objects.get(name="Yedek Parça")
        spare_part_items = ItemMaster.objects.filter(stock_type=spare_part_stock_type).exclude(pk=item.pk).order_by('shortcode', 'name')
    except StockType.DoesNotExist:
        spare_part_items = ItemMaster.objects.none()
    
    context = {
        'item': item,
        'categories': categories,
        'brands': brands,
        'stock_types': stock_types,
        'statuses': statuses,
        'warranty_values': warranty_values,
        'service_forms': service_forms,
        'service_period_values': service_period_values,
        'current_maintenance_schedules': current_maintenance_schedules,
        'spare_part_items': spare_part_items,
    }
    return render(request, 'pages/itemmaster/item-master-update.html', context)

@login_required(login_url='login')
@permission_required('item_master.add_inventoryitem', raise_exception=True)
def inventory_item_create(request):
    from django.utils.translation import gettext as _
    from django.contrib import messages
    import uuid
    
    if request.method == 'POST':
        try:
            # Get the item master
            item_master_id = request.POST.get('item_master')
            if not item_master_id:
                messages.error(request, _('Please select an item master.'))
                return redirect('item-master:inventory_item_create')
                
            item_master = get_object_or_404(ItemMaster, id=item_master_id)
            
            # Create inventory item
            inventory_item = InventoryItem.objects.create(
                name=item_master,
                serial_no=request.POST.get('serial_no', ''),
                in_used=request.POST.get('in_used') == 'on',
                created_by=request.user
            )
            
            # Handle attributes
            attribute_types = request.POST.getlist('attribute_type')
            attribute_values = request.POST.getlist('attribute_value')
            attribute_units = request.POST.getlist('attribute_unit')
            
            for i, attr_type_id in enumerate(attribute_types):
                if attr_type_id and i < len(attribute_values) and attribute_values[i]:
                    try:
                        attr_type = AttributeType.objects.get(id=attr_type_id)
                        unit = None
                        
                        # Get unit from form data
                        if i < len(attribute_units) and attribute_units[i]:
                            unit = AttributeUnit.objects.get(id=attribute_units[i])
                            # Validate that the unit is compatible with the attribute type
                            if not AttributeTypeUnit.objects.filter(
                                attribute_type=attr_type,
                                attribute_unit=unit
                            ).exists():
                                unit = None
                        
                        # If no unit specified or unit is incompatible, try to use default unit
                        if not unit:
                            default_type_unit = AttributeTypeUnit.objects.filter(
                                attribute_type=attr_type,
                                is_default=True
                            ).first()
                            if default_type_unit:
                                unit = default_type_unit.attribute_unit
                        
                        InventoryItemAttribute.objects.create(
                            inventory_item=inventory_item,
                            attribute_type=attr_type,
                            value=attribute_values[i],
                            unit=unit
                        )
                    except (AttributeType.DoesNotExist, AttributeUnit.DoesNotExist):
                        continue
            
            messages.success(request, _('Inventory item created successfully.'))
            return redirect('item-master:inventory_item_detail', pk=inventory_item.pk)
            
        except Exception as e:
            messages.error(request, _('An error occurred while creating the inventory item: {}').format(str(e)))
    
    # GET request - display form
    # Filter item masters for stock_type "Ticari" only
    try:
        ticari_stock_type = StockType.objects.get(name="Ticari")
        item_masters = ItemMaster.objects.filter(
            stock_type=ticari_stock_type
        ).select_related(
            'category', 'brand_name', 'stock_type', 'status'
        ).order_by('shortcode', 'name')
        
        print(f"Found {item_masters.count()} items with stock_type 'Ticari'")
        
    except StockType.DoesNotExist:
        print("Stock type 'Ticari' not found")
        # Fallback to all item masters if "Ticari" doesn't exist
        item_masters = ItemMaster.objects.select_related(
            'category', 'brand_name', 'stock_type', 'status'
        ).order_by('shortcode', 'name')
        
        print(f"Fallback: Using all {item_masters.count()} item masters")
    
    # Debug: Print first few items
    for item in item_masters[:3]:
        print(f"Item: {item.shortcode} - {item.name} - Stock Type: {item.stock_type.name if item.stock_type else 'No Stock Type'}")
    
    attribute_types = AttributeType.objects.all().order_by('name')
    attribute_units = AttributeUnit.objects.all().order_by('name')
    
    context = {
        'item_masters': item_masters,
        'attribute_types': attribute_types,
        'attribute_units': attribute_units,
    }
    return render(request, 'pages/inventory/inventory-item-create.html', context)


@login_required
@permission_required('item_master.change_inventoryitem', raise_exception=True)
def inventory_item_update(request, pk):
    """Update an existing inventory item"""
    from django.contrib import messages
    from django.utils.translation import gettext as _
    
    try:
        inventory_item = get_object_or_404(InventoryItem, pk=pk)
    except InventoryItem.DoesNotExist:
        messages.error(request, _('Inventory item not found.'))
        return redirect('item-master:inventory_item_list')
    
    # Check if distributor or sales manager user has access to this item
    user = request.user
    if hasattr(user, 'role') and user.role in ['manager_distributor', 'service_distributor']:
        if hasattr(user, 'company') and user.company:
            from warranty_and_services.utils import get_user_accessible_companies
            accessible_company_ids = get_user_accessible_companies(user)
            
            # Check if this item is installed at any accessible company
            from warranty_and_services.models import Installation
            item_installations = Installation.objects.filter(
                inventory_item=inventory_item,
                customer_id__in=accessible_company_ids
            )
            
            if not item_installations.exists():
                messages.error(request, _('You don\'t have permission to update this item.'))
                return redirect('item-master:inventory_item_list')
        else:
            messages.error(request, _('Your company information is not defined.'))
            return redirect('item-master:inventory_item_list')
    elif hasattr(user, 'role') and user.role == 'sales_manager':
        # Sales manager can update:
        # 1. Available items (in_used=False)
        # 2. In-use items installed at accessible companies
        if inventory_item.in_used:  # If item is in use, check accessibility
            if hasattr(user, 'company') and user.company:
                from warranty_and_services.utils import get_user_accessible_companies
                accessible_company_ids = get_user_accessible_companies(user)
                
                from warranty_and_services.models import Installation
                item_installations = Installation.objects.filter(
                    inventory_item=inventory_item,
                    customer_id__in=accessible_company_ids
                )
                
                if not item_installations.exists():
                    messages.error(request, _('You don\'t have permission to update this item.'))
                    return redirect('item-master:inventory_item_list')
            else:
                messages.error(request, _('Your company information is not defined.'))
                return redirect('item-master:inventory_item_list')
        # If item is available (in_used=False), sales manager can always update it
    
    if request.method == 'POST':
        try:
            # Get form data
            item_master_id = request.POST.get('item_master')
            quantity = request.POST.get('quantity', 1)
            serial_no = request.POST.get('serial_no', '')
            in_used = request.POST.get('in_used') == 'on'
            
            # Validate required fields
            if not item_master_id:
                messages.error(request, _('Please select an item master.'))
                return redirect('item-master:inventory_item_update', pk=pk)
            
            # Get item master
            try:
                item_master = ItemMaster.objects.get(id=item_master_id)
            except ItemMaster.DoesNotExist:
                messages.error(request, _('Selected item master does not exist.'))
                return redirect('item-master:inventory_item_update', pk=pk)
            
            # Update inventory item
            inventory_item.name = item_master
            inventory_item.quantity = int(quantity) if quantity else 1
            inventory_item.serial_no = serial_no
            inventory_item.in_used = in_used
            inventory_item.save()
            
            # Handle attributes - delete existing and create new ones
            InventoryItemAttribute.objects.filter(inventory_item=inventory_item).delete()
            
            # Get attribute data
            attribute_types = request.POST.getlist('attribute_type[]')
            attribute_values = request.POST.getlist('attribute_value[]')
            attribute_units = request.POST.getlist('attribute_unit[]')
            
            # Create new attributes
            for i, attr_type_id in enumerate(attribute_types):
                if attr_type_id and i < len(attribute_values) and attribute_values[i]:
                    try:
                        attr_type = AttributeType.objects.get(id=attr_type_id)
                        unit = None
                        
                        # Get unit from form data
                        if i < len(attribute_units) and attribute_units[i]:
                            unit = AttributeUnit.objects.get(id=attribute_units[i])
                            # Validate that the unit is compatible with the attribute type
                            if not AttributeTypeUnit.objects.filter(
                                attribute_type=attr_type,
                                attribute_unit=unit
                            ).exists():
                                messages.warning(
                                    request, 
                                    _(f'Unit "{unit.name}" is not compatible with attribute type "{attr_type.name}". Using default unit instead.')
                                )
                                unit = None
                        
                        # If no unit specified or unit is incompatible, try to use default unit
                        if not unit:
                            default_type_unit = AttributeTypeUnit.objects.filter(
                                attribute_type=attr_type,
                                is_default=True
                            ).first()
                            if default_type_unit:
                                unit = default_type_unit.attribute_unit
                        
                        InventoryItemAttribute.objects.create(
                            inventory_item=inventory_item,
                            attribute_type=attr_type,
                            value=attribute_values[i],
                            unit=unit
                        )
                    except (AttributeType.DoesNotExist, AttributeUnit.DoesNotExist):
                        continue
            
            messages.success(request, _('Inventory item updated successfully.'))
            return redirect('item-master:inventory_item_detail', pk=inventory_item.pk)
            
        except Exception as e:
            messages.error(request, _('An error occurred while updating the inventory item: {}').format(str(e)))
    
    # GET request - display form with current data
    # Filter item masters for stock_type "Ticari" only
    try:
        ticari_stock_type = StockType.objects.get(name="Ticari")
        item_masters = ItemMaster.objects.filter(
            stock_type=ticari_stock_type
        ).select_related(
            'category', 'brand_name', 'stock_type', 'status'
        ).order_by('shortcode', 'name')
        
    except StockType.DoesNotExist:
        # Fallback to all item masters if "Ticari" doesn't exist
        item_masters = ItemMaster.objects.select_related(
            'category', 'brand_name', 'stock_type', 'status'
        ).order_by('shortcode', 'name')
    
    attribute_types = AttributeType.objects.all().order_by('name')
    attribute_units = AttributeUnit.objects.all().order_by('name')
    
    # Get current attributes for the inventory item
    current_attributes = InventoryItemAttribute.objects.filter(
        inventory_item=inventory_item
    ).select_related('attribute_type', 'unit')
    
    context = {
        'inventory_item': inventory_item,
        'item_masters': item_masters,
        'attribute_types': attribute_types,
        'attribute_units': attribute_units,
        'current_attributes': current_attributes,
        'is_update': True,
    }
    return render(request, 'pages/inventory/inventory-item-update.html', context)


@login_required
def inventory_item_delete(request, pk):
    """Delete an inventory item"""
    from django.contrib import messages
    from django.utils.translation import gettext as _
    
    try:
        inventory_item = get_object_or_404(InventoryItem, pk=pk)
    except InventoryItem.DoesNotExist:
        messages.error(request, _('Inventory item not found.'))
        return redirect('item-master:inventory_item_list')
    
    # Check if distributor or sales manager user has access to this item
    user = request.user
    if hasattr(user, 'role') and user.role in ['manager_distributor', 'service_distributor']:
        if hasattr(user, 'company') and user.company:
            from warranty_and_services.utils import get_user_accessible_companies
            accessible_company_ids = get_user_accessible_companies(user)
            
            # Check if this item is installed at any accessible company
            from warranty_and_services.models import Installation
            item_installations = Installation.objects.filter(
                inventory_item=inventory_item,
                customer_id__in=accessible_company_ids
            )
            
            if not item_installations.exists():
                messages.error(request, _('You don\'t have permission to access this item.'))
                return redirect('item-master:inventory_item_list')
        else:
            messages.error(request, _('Your company information is not defined.'))
            return redirect('item-master:inventory_item_list')
    elif hasattr(user, 'role') and user.role == 'sales_manager':
        # Sales manager can delete:
        # 1. Available items (in_used=False)
        # 2. In-use items installed at accessible companies
        if inventory_item.in_used:  # If item is in use, check accessibility
            if hasattr(user, 'company') and user.company:
                from warranty_and_services.utils import get_user_accessible_companies
                accessible_company_ids = get_user_accessible_companies(user)
                
                from warranty_and_services.models import Installation
                item_installations = Installation.objects.filter(
                    inventory_item=inventory_item,
                    customer_id__in=accessible_company_ids
                )
                
                if not item_installations.exists():
                    messages.error(request, _('You don\'t have permission to access this item.'))
                    return redirect('item-master:inventory_item_list')
            else:
                messages.error(request, _('Your company information is not defined.'))
                return redirect('item-master:inventory_item_list')
        # If item is available (in_used=False), sales manager can always delete it
    
    if request.method == 'POST':
        try:
            inventory_item_name = inventory_item.name.name
            inventory_item_serial = inventory_item.serial_no
            inventory_item.delete()
            messages.success(request, _('Inventory item "{} ({})" has been deleted successfully.').format(inventory_item_name, inventory_item_serial))
            return redirect('item-master:inventory_item_list')
        except Exception as e:
            messages.error(request, _('An error occurred while deleting the inventory item: {}').format(str(e)))
            return redirect('item-master:inventory_item_detail', pk=pk)
    
    # GET request - show confirmation page
    context = {
        'inventory_item': inventory_item,
    }
    return render(request, 'pages/inventory/inventory-item-delete.html', context)


def get_attribute_units(request):
    """AJAX view to get units for a specific attribute type"""
    attribute_type_id = request.GET.get('attribute_type_id')
    
    if not attribute_type_id:
        return JsonResponse({'units': []})
    
    try:
        type_units = AttributeTypeUnit.objects.filter(
            attribute_type_id=attribute_type_id
        ).select_related('attribute_unit').order_by('-is_default', 'attribute_unit__name')
        
        units_list = [
            {
                'id': type_unit.attribute_unit.id,
                'name': type_unit.attribute_unit.name,
                'symbol': type_unit.attribute_unit.symbol,
                'is_default': type_unit.is_default,
                'display': f"{type_unit.attribute_unit.name} ({type_unit.attribute_unit.symbol})"
            }
            for type_unit in type_units
        ]
        
        return JsonResponse({'units': units_list})
    except Exception as e:
        return JsonResponse({'units': [], 'error': str(e)})




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_search_api(request):
    """
    QR kod ile ekipman arama API'si - warranty_and_services mantığı
    """
    try:
        qr_code = request.GET.get('qr_code', '').strip()
        serial_no = request.GET.get('serial_no', '').strip()
        
        # QR kod veya seri no ile arama
        search_term = qr_code or serial_no
        
        if not search_term:
            return Response({
                'success': False,
                'message': 'QR kod veya seri numarası gerekli'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ekipman ara - sadece kullanılmayan (in_used=False) olanlar arasından
        try:
            item = InventoryItem.objects.select_related(
                'name', 
                'name__category', 
                'name__brand_name'
            ).get(serial_no=search_term, in_used=False)
            
            # Basit response - warranty_and_services tarzı
            return Response({
                'success': True,
                'message': 'Ekipman Bulundu',
                'equipment': {
                    'name': item.name.name if item.name else 'Bilinmiyor',
                    'brand': item.name.brand_name.name if item.name and item.name.brand_name else 'Bilinmiyor',
                    'category': item.name.category.category_name if item.name and item.name.category else 'Bilinmiyor',
                    'serial_no': item.serial_no or 'Seri No Yok',
                    'in_use': item.in_used
                }
            }, status=status.HTTP_200_OK)
            
        except InventoryItem.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Bu seri numarası ile kullanılabilir ekipman bulunamadı'
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Arama hatası: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Create your views here.
