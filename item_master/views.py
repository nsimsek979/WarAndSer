
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import ItemMaster, Category, Brand, StockType

@login_required(login_url='login')
def item_master_list(request):
    from django.utils.translation import gettext as _
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get filter parameters
    category_filter = request.GET.get('category', '')
    brand_filter = request.GET.get('brand', '')
    stock_type_filter = request.GET.get('stock_type', '')
    
    # Start with all items
    items = ItemMaster.objects.select_related('category', 'brand_name', 'stock_type', 'status').all()
    
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
    }
    return render(request, 'pages/itemmaster/item-master-list.html', context)

@login_required(login_url='login')
def item_master_detail(request, pk):
    item = get_object_or_404(
        ItemMaster.objects.select_related(
            'category', 'brand_name', 'stock_type', 'status'
        ).prefetch_related(
            'images', 'warranties', 'service_forms', 'specs'
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
                
                messages.success(request, f'Item "{item.name}" created successfully!')
                return redirect('item-master:item_master_detail', pk=item.pk)
                
            except Exception as e:
                messages.error(request, f'Error creating item: {str(e)}')
    
    # Get filter options for form
    from .models import Status, WarrantyValue, ServiceForm
    categories = Category.objects.all().order_by('category_name')
    brands = Brand.objects.all().order_by('name')
    stock_types = StockType.objects.all().order_by('name')
    statuses = Status.objects.all().order_by('status')
    
    # Get existing warranty values and service forms for selection
    warranty_values = WarrantyValue.objects.select_related('warranty_type').all().order_by('warranty_type__type', 'value')
    service_forms = ServiceForm.objects.all().order_by('name')
    
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
        'spare_part_items': spare_part_items,
    }
    return render(request, 'pages/itemmaster/item-master-create.html', context)

@login_required(login_url='login')
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
                
                messages.success(request, f'Item "{item.name}" updated successfully!')
                return redirect('item-master:item_master_detail', pk=item.pk)
                
            except Exception as e:
                messages.error(request, f'Error updating item: {str(e)}')
    
    # Get filter options for form
    from .models import Status, WarrantyValue, ServiceForm
    categories = Category.objects.all().order_by('category_name')
    brands = Brand.objects.all().order_by('name')
    stock_types = StockType.objects.all().order_by('name')
    statuses = Status.objects.all().order_by('status')
    
    # Get existing warranty values and service forms for selection
    warranty_values = WarrantyValue.objects.select_related('warranty_type').all().order_by('warranty_type__type', 'value')
    service_forms = ServiceForm.objects.all().order_by('name')
    
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
        'spare_part_items': spare_part_items,
    }
    return render(request, 'pages/itemmaster/item-master-update.html', context)


# Create your views here.
