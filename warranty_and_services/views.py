from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count, Case, When, IntegerField
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
import json
from datetime import datetime, timedelta
from .models import Installation, WarrantyFollowUp, ServiceFollowUp, InstallationImage, InstallationDocument


@login_required
def warranty_tracking_list(request):
    """
    Warranty takip listesi - aktif, süresi yaklaşan ve süresi geçen garantiler
    """
    # Filtreler
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    warranties = WarrantyFollowUp.objects.select_related(
        'installation__customer',
        'installation__inventory_item__name'
    ).order_by('end_of_warranty_date')
    
    # Arama filtresi
    if search_query:
        warranties = warranties.filter(
            Q(installation__customer__name__icontains=search_query) |
            Q(installation__inventory_item__name__name__icontains=search_query) |
            Q(installation__inventory_item__serial_no__icontains=search_query)
        )
    
    # Tarih filtreleri
    now = timezone.now()
    if filter_type == 'active':
        warranties = warranties.filter(end_of_warranty_date__gt=now)
    elif filter_type == 'expiring_soon':
        # 30 gün içinde süresi dolacak
        thirty_days = now + timedelta(days=30)
        warranties = warranties.filter(
            end_of_warranty_date__gt=now,
            end_of_warranty_date__lte=thirty_days
        )
    elif filter_type == 'expired':
        warranties = warranties.filter(end_of_warranty_date__lte=now)
    
    # Pagination
    paginator = Paginator(warranties, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # İstatistikler
    stats = {
        'total': WarrantyFollowUp.objects.count(),
        'active': WarrantyFollowUp.objects.filter(end_of_warranty_date__gt=now).count(),
        'expiring_soon': WarrantyFollowUp.objects.filter(
            end_of_warranty_date__gt=now,
            end_of_warranty_date__lte=now + timedelta(days=30)
        ).count(),
        'expired': WarrantyFollowUp.objects.filter(end_of_warranty_date__lte=now).count(),
    }
    
    context = {
        'warranties': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'stats': stats,
        'filter_type': filter_type,
        'search_query': search_query,
    }
    
    return render(request, 'warranty_and_services/warranty_tracking_list.html', context)


@login_required
def service_tracking_list(request):
    """
    Servis takip listesi - planlanan, geciken ve tamamlanan servisler
    """
    # Filtreler
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    services = ServiceFollowUp.objects.select_related(
        'installation__customer',
        'installation__inventory_item__name'
    ).order_by('next_service_date')
    
    # Arama filtresi
    if search_query:
        services = services.filter(
            Q(installation__customer__name__icontains=search_query) |
            Q(installation__inventory_item__name__name__icontains=search_query) |
            Q(installation__inventory_item__serial_no__icontains=search_query)
        )
    
    # Durum filtreleri
    now = timezone.now()
    if filter_type == 'pending':
        services = services.filter(is_completed=False, next_service_date__gt=now)
    elif filter_type == 'due_soon':
        # 7 gün içinde yapılması gereken
        seven_days = now + timedelta(days=7)
        services = services.filter(
            is_completed=False,
            next_service_date__gt=now,
            next_service_date__lte=seven_days
        )
    elif filter_type == 'overdue':
        services = services.filter(is_completed=False, next_service_date__lte=now)
    elif filter_type == 'completed':
        services = services.filter(is_completed=True)
    
    # Pagination
    paginator = Paginator(services, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # İstatistikler
    stats = {
        'total': ServiceFollowUp.objects.count(),
        'pending': ServiceFollowUp.objects.filter(is_completed=False, next_service_date__gt=now).count(),
        'due_soon': ServiceFollowUp.objects.filter(
            is_completed=False,
            next_service_date__gt=now,
            next_service_date__lte=now + timedelta(days=7)
        ).count(),
        'overdue': ServiceFollowUp.objects.filter(is_completed=False, next_service_date__lte=now).count(),
        'completed': ServiceFollowUp.objects.filter(is_completed=True).count(),
    }
    
    context = {
        'services': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'stats': stats,
        'filter_type': filter_type,
        'search_query': search_query,
    }
    
    return render(request, 'warranty_and_services/service_tracking_list.html', context)


@login_required
def warranty_detail(request, warranty_id):
    """
    Warranty detay sayfası - installation detail'a yönlendirir
    """
    warranty = get_object_or_404(WarrantyFollowUp, id=warranty_id)
    return redirect('warranty_and_services:installation_detail', installation_id=warranty.installation.id)


@login_required
def service_detail(request, service_id):
    """
    Servis detay sayfası - installation detail'a yönlendirir
    """
    service = get_object_or_404(ServiceFollowUp, id=service_id)
    return redirect('warranty_and_services:installation_detail', installation_id=service.installation.id)


@login_required
def installation_detail(request, installation_id):
    """
    Installation detay sayfası - tüm garanti ve servis bilgileri ile
    """
    installation = get_object_or_404(
        Installation.objects.select_related(
            'customer',
            'customer__working_hours',
            'customer__related_company',
            'customer__related_manager',
            'customer__core_business',
            'inventory_item',
            'inventory_item__name',
            'inventory_item__name__category',
            'user'
        ).prefetch_related(
            'warranty_followups',
            'service_followups',
            'images',
            'documents',
            'customer__address',
            'customer__contactperson_set'
        ),
        id=installation_id
    )
    
    customer = installation.customer
    inventory_item = installation.inventory_item
    warranties = installation.warranty_followups.all()
    services = installation.service_followups.all()
    
    context = {
        'installation': installation,
        'customer': customer,
        'inventory_item': inventory_item,
        'warranties': warranties,
        'services': services,
    }
    return render(request, 'warranty_and_services/installation_detail.html', context)


class InstallationListView(LoginRequiredMixin, ListView):
    """
    Kurulum listesi view'ı
    """
    model = Installation
    template_name = 'warranty_and_services/installation_list.html'
    context_object_name = 'installations'
    paginate_by = 20
    
    def get_queryset(self):
        from django.db.models import Min
        
        # Queryset'i oluştur
        queryset = Installation.objects.select_related(
            'customer',
            'inventory_item__name'
        ).prefetch_related(
            'warranty_followups',
            'service_followups'
        ).annotate(
            next_warranty_end=Min('warranty_followups__end_of_warranty_date'),
            next_service_date=Min('service_followups__next_service_date')
        ).order_by('-setup_date')
        
        # Arama filtresi
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(customer__name__icontains=search_query) |
                Q(inventory_item__name__name__icontains=search_query) |
                Q(inventory_item__serial_no__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


# Mobile Installation Views
@login_required
def mobile_installation_scanner(request):
    """
    Mobil kurulum scanner sayfası
    """
    return render(request, 'warranty_and_services/mobile/installation_scanner.html')


@login_required  
def mobile_installation_form(request):
    """
    Mobil kurulum formu sayfası
    """
    item_id = request.GET.get('item_id')
    if not item_id:
        return redirect('warranty_and_services:mobile_installation_scanner')
    
    # Item_master modülünden inventory item'ı al
    from item_master.models import InventoryItem
    try:
        inventory_item = InventoryItem.objects.select_related('name').get(id=item_id)
    except InventoryItem.DoesNotExist:
        return redirect('warranty_and_services:mobile_installation_scanner')
    
    context = {
        'inventory_item': inventory_item,
    }
    return render(request, 'warranty_and_services/mobile/installation_form.html', context)


# API Endpoints for Mobile
@csrf_exempt
@require_http_methods(["POST"])
def api_search_by_barcode(request):
    """
    QR kod ile ürün arama API endpoint'i
    """
    try:
        data = json.loads(request.body)
        qr_code = data.get('barcode', '').strip()  # Frontend'den 'barcode' olarak geliyor ama QR code
        
        if not qr_code:
            return JsonResponse({
                'success': False,
                'message': 'QR kodu gerekli'
            })
        
        # Item_master modülünden InventoryItem'ı bul
        from item_master.models import InventoryItem
        try:
            # QR code formatı: "ID:{id}|CODE:{serial}|NAME:{name}|SERIAL:{serial}"
            # QR string'ini parse et
            inventory_item = None
            
            if 'ID:' in qr_code and '|' in qr_code:
                # QR kod formatını parse et
                parts = qr_code.split('|')
                id_part = [part for part in parts if part.startswith('ID:')]
                if id_part:
                    item_id = id_part[0].replace('ID:', '')
                    inventory_item = InventoryItem.objects.select_related('name', 'name__brand_name', 'name__category').get(id=item_id)
                else:
                    # ID bulunamadı, serial ile dene
                    serial_part = [part for part in parts if part.startswith('SERIAL:')]
                    if serial_part:
                        serial_no = serial_part[0].replace('SERIAL:', '')
                        inventory_item = InventoryItem.objects.select_related('name', 'name__brand_name', 'name__category').get(serial_no=serial_no)
            else:
                # QR formatı farklı, direkt serial number olarak dene
                inventory_item = InventoryItem.objects.select_related('name', 'name__brand_name', 'name__category').get(serial_no=qr_code)
            
            if not inventory_item:
                raise InventoryItem.DoesNotExist
            
            # Check if item is already installed/in use
            is_installed = Installation.objects.filter(inventory_item=inventory_item).exists()
            
            # Item bilgilerini dön
            return JsonResponse({
                'success': True,
                'item': {
                    'id': inventory_item.id,
                    'name': inventory_item.name.name if inventory_item.name else 'N/A',
                    'model': inventory_item.name.name if inventory_item.name else 'N/A',  # ItemMaster'da model field yok
                    'brand': inventory_item.name.brand_name.name if inventory_item.name and inventory_item.name.brand_name else 'N/A',
                    'category': inventory_item.name.category.category_name if inventory_item.name and inventory_item.name.category else 'N/A',
                    'serial_number': inventory_item.serial_no or 'N/A',
                    'is_installed': is_installed,
                    'in_used': inventory_item.in_used,
                    'qr_code': qr_code,
                    'image': inventory_item.qr_code_image.url if inventory_item.qr_code_image else None,
                }
            })
            
        except InventoryItem.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Bu QR kodu ile eşleşen ürün bulunamadı'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Geçersiz JSON formatı'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Arama sırasında bir hata oluştu: {str(e)}'
        })


@csrf_exempt
@require_http_methods(["POST"])
def api_search_by_serial(request):
    """
    Seri numarası ile ürün arama API endpoint'i
    """
    try:
        data = json.loads(request.body)
        serial_number = data.get('serial_number', '').strip()
        
        if not serial_number:
            return JsonResponse({
                'success': False,
                'message': 'Seri numarası gerekli'
            })
        
        # Item_master modülünden InventoryItem'ı bul
        from item_master.models import InventoryItem
        try:
            inventory_item = InventoryItem.objects.select_related('name', 'name__brand_name', 'name__category').get(
                serial_no=serial_number
            )
            
            # Check if item is already installed/in use
            is_installed = Installation.objects.filter(inventory_item=inventory_item).exists()
            
            # Item bilgilerini dön
            return JsonResponse({
                'success': True,
                'item': {
                    'id': inventory_item.id,
                    'name': inventory_item.name.name if inventory_item.name else 'N/A',
                    'model': inventory_item.name.name if inventory_item.name else 'N/A',  # ItemMaster'da model field yok
                    'brand': inventory_item.name.brand_name.name if inventory_item.name and inventory_item.name.brand_name else 'N/A',
                    'category': inventory_item.name.category.category_name if inventory_item.name and inventory_item.name.category else 'N/A',
                    'serial_number': inventory_item.serial_no or 'N/A',
                    'is_installed': is_installed,
                    'in_used': inventory_item.in_used,
                    'qr_code': f"ID:{inventory_item.id}|SERIAL:{inventory_item.serial_no}",
                    'image': inventory_item.qr_code_image.url if inventory_item.qr_code_image else None,
                }
            })
            
        except InventoryItem.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Bu seri numarası ile eşleşen ürün bulunamadı'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Geçersiz JSON formatı'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Arama sırasında bir hata oluştu: {str(e)}'
        })
        
        # Item_master modülünden InventoryItem'ı bul
        from item_master.models import InventoryItem
        try:
            inventory_item = InventoryItem.objects.select_related('name').get(
                serial_no=serial_number
            )
            
            # Item bilgilerini dön
            return JsonResponse({
                'success': True,
                'item': {
                    'id': inventory_item.id,
                    'name': inventory_item.name.name if inventory_item.name else 'N/A',
                    'model': inventory_item.model or 'N/A',
                    'barcode': inventory_item.barcode or 'N/A',
                    'serial_number': inventory_item.serial_no or 'N/A',
                    'qr_code': inventory_item.qr_code or 'N/A',
                }
            })
            
        except InventoryItem.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Bu seri numarası ile eşleşen ürün bulunamadı'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Geçersiz JSON formatı'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Arama sırasında bir hata oluştu'
        })


# Mobile Installation Views
def mobile_installation_scanner(request):
    """Mobile installation scanner page"""
    return render(request, 'warranty_and_services/mobile/installation_scanner.html')


def mobile_installation_form(request):
    """Mobile installation form page"""
    item_id = request.GET.get('item_id')
    if not item_id:
        return redirect('warranty_and_services:mobile_installation_scanner')
    
    # Get the item
    from item_master.models import InventoryItem
    try:
        item = InventoryItem.objects.select_related('name').get(id=item_id)
    except InventoryItem.DoesNotExist:
        return redirect('warranty_and_services:mobile_installation_scanner')
    
    # Check if item is already installed
    is_already_installed = Installation.objects.filter(inventory_item=item).exists()
    
    # If item is already installed, redirect back to scanner with error
    if is_already_installed or item.in_used:
        messages.error(request, 'Bu ürün zaten kurulmuş veya kullanımda. Kurulum yapılamaz.')
        return redirect('warranty_and_services:mobile_installation_scanner')
    
    context = {
        'item': item
    }
    return render(request, 'warranty_and_services/mobile/installation_form.html', context)


# Customer API Endpoints
@csrf_exempt
@require_http_methods(["POST"])
def api_customer_search(request):
    """Customer search API endpoint - searches in user's company hierarchy"""
    try:
        data = json.loads(request.body)
        search_query = data.get('search', '').strip()
        
        if len(search_query) < 2:
            return JsonResponse({
                'success': False,
                'message': 'En az 2 karakter girin'
            })
        
        from customer.models import Company
        
        # Get user's company and build hierarchy
        user = request.user
        user_company = None
        if hasattr(user, 'company') and user.company:
            user_company = user.company
        
        if not user_company:
            return JsonResponse({
                'success': False,
                'message': 'Kullanıcının bağlı olduğu firma bulunamadı'
            })
        
        # Build company hierarchy: user's company + child companies + child's child companies
        company_ids = [user_company.id]
        
        # Get direct child companies
        child_companies = Company.objects.filter(related_company=user_company)
        for child in child_companies:
            company_ids.append(child.id)
            
            # Get child's child companies (grandchildren)
            grandchild_companies = Company.objects.filter(related_company=child)
            for grandchild in grandchild_companies:
                company_ids.append(grandchild.id)
        
        print(f"User company: {user_company.name}")
        print(f"Searching in company hierarchy: {company_ids}")
        
        # Search customers within the company hierarchy
        customers = Company.objects.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(tax_number__icontains=search_query),
            id__in=company_ids,
            company_type='enduser',  # Only end users
            active=True
        ).order_by('name')[:10]  # Limit to 10 results
        
        customer_list = []
        for customer in customers:
            customer_list.append({
                'id': customer.id,
                'name': customer.name,
                'email': customer.email or '',
                'telephone': customer.telephone or '',
                'tax_number': customer.tax_number or '',
                'company_type_display': customer.get_company_type_display(),
                'related_company': customer.related_company.name if customer.related_company else ''
            })
        
        print(f"Found {len(customer_list)} customers")
        
        return JsonResponse({
            'success': True,
            'customers': customer_list
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Geçersiz JSON formatı'
        })
    except Exception as e:
        print(f"Customer search error: {e}")  # Debug
        return JsonResponse({
            'success': False,
            'message': f'Arama sırasında bir hata oluştu: {str(e)}'
        })


@csrf_exempt
@require_http_methods(["POST"])
def api_customer_create(request):
    """Customer creation API endpoint"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if not data.get('name', '').strip():
            return JsonResponse({
                'success': False,
                'message': 'Firma adı gereklidir'
            })
        
        from customer.models import Company, ContactPerson, Address
        
        # Get user's related company (distributor)
        user = request.user
        related_company = None
        related_manager = None
        
        if hasattr(user, 'company') and user.company:
            # New customer will be child of user's company
            related_company = user.company
            # Set related_manager to user's company's related_manager
            if user.company.related_manager:
                related_manager = user.company.related_manager
        
        if not related_company:
            return JsonResponse({
                'success': False,
                'message': 'Kullanıcının bağlı olduğu firma bulunamadı'
            })
        
        print(f"Creating customer for user company: {related_company.name}")
        
        # Create new customer
        customer = Company.objects.create(
            name=data['name'].strip(),
            tax_number=data.get('tax_number', '').strip() or None,
            email=data.get('email', '').strip() or None,
            telephone=data.get('telephone', '').strip() or None,
            company_type='enduser',
            related_company=related_company,  # Child of user's company
            related_manager=related_manager,  # Same as user's company's manager
            active=True
        )
        
        # Create contact person if provided
        contact_person_name = data.get('contact_person', '').strip()
        contact_phone = data.get('contact_phone', '').strip()
        contact_email = data.get('contact_email', '').strip()
        
        if contact_person_name:
            ContactPerson.objects.create(
                company=customer,
                full_name=contact_person_name,
                email=contact_email or customer.email,
                telephone=contact_phone or customer.telephone
            )
        
        # Create address if provided
        address_text = data.get('address', '').strip()
        city = data.get('city', '').strip()
        
        if address_text:
            address_name = 'Merkez'
            if city:
                address_name = f"Merkez - {city}"
                
            Address.objects.create(
                company=customer,
                name=address_name,
                address=address_text
            )
        
        return JsonResponse({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'telephone': customer.telephone,
                'tax_number': customer.tax_number,
                'company_type_display': customer.get_company_type_display()
            },
            'message': 'Müşteri başarıyla oluşturuldu'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Geçersiz JSON formatı'
        })
    except Exception as e:
        print(f"Customer creation error: {e}")  # Debug
        return JsonResponse({
            'success': False,
            'message': 'Müşteri oluşturulurken bir hata oluştu'
        })


@csrf_exempt
@require_http_methods(["POST"])
def api_installation_create(request):
    """Installation creation API endpoint with file uploads"""
    try:
        # Handle both JSON and FormData
        if request.content_type and 'application/json' in request.content_type:
            data = json.loads(request.body)
        else:
            # FormData
            data = dict(request.POST)
            # Convert single-item lists to strings
            for key, value in data.items():
                if isinstance(value, list) and len(value) == 1:
                    data[key] = value[0]
        
        # Validate required fields
        if not data.get('item_id'):
            return JsonResponse({
                'success': False,
                'message': 'Ürün ID gereklidir'
            })
        
        if not data.get('customer_id'):
            return JsonResponse({
                'success': False,
                'message': 'Müşteri ID gereklidir'
            })
        
        if not data.get('setup_date'):
            return JsonResponse({
                'success': False,
                'message': 'Kurulum tarihi gereklidir'
            })
        
        from item_master.models import InventoryItem
        from customer.models import Company
        from datetime import datetime
        
        # Get item and customer
        try:
            item = InventoryItem.objects.get(id=data['item_id'])
            customer = Company.objects.get(id=data['customer_id'])
        except (InventoryItem.DoesNotExist, Company.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'Ürün veya müşteri bulunamadı'
            })
        
        # Check if item is already in use
        if item.in_used:
            return JsonResponse({
                'success': False,
                'message': 'Bu ürün zaten kullanımda'
            })
        
        # Parse setup date
        try:
            setup_date = datetime.fromisoformat(data['setup_date'].replace('Z', '+00:00'))
            # Make timezone aware if it's naive
            if setup_date.tzinfo is None:
                setup_date = timezone.make_aware(setup_date)
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Geçersiz tarih formatı'
            })
        
        # Check if setup date is in the future
        current_time = timezone.now()
        if setup_date > current_time:
            return JsonResponse({
                'success': False,
                'message': 'Kurulum tarihi bugünden ileri olamaz'
            })
        
        # Create installation
        installation = Installation.objects.create(
            user=request.user,
            setup_date=setup_date,
            inventory_item=item,
            customer=customer,
            location_latitude=data.get('location_latitude'),
            location_longitude=data.get('location_longitude'),
            location_address=data.get('location_address', '').strip(),
            installation_notes=data.get('installation_notes', '').strip()
        )
        
        # Mark item as in use
        item.in_used = True
        item.save()
        
        # Handle file uploads
        uploaded_photos = []
        uploaded_files = []
        
        # Handle photos
        if 'photos' in request.FILES:
            photos = request.FILES.getlist('photos')
            for photo in photos:
                # Validate photo
                if not photo.content_type.startswith('image/'):
                    continue
                if photo.size > 5 * 1024 * 1024:  # 5MB limit
                    continue
                    
                installation_image = InstallationImage.objects.create(
                    installation=installation,
                    image=photo,
                    description=f"Kurulum fotoğrafı - {photo.name}",
                    uploaded_by=request.user
                )
                uploaded_photos.append({
                    'id': installation_image.id,
                    'name': photo.name,
                    'url': installation_image.image.url if installation_image.image else None
                })
        
        # Handle files/documents
        if 'files' in request.FILES:
            files = request.FILES.getlist('files')
            for file in files:
                # Validate file
                if file.size > 10 * 1024 * 1024:  # 10MB limit
                    continue
                    
                installation_doc = InstallationDocument.objects.create(
                    installation=installation,
                    document=file,
                    description=f"Kurulum dökümanı - {file.name}",
                    uploaded_by=request.user
                )
                uploaded_files.append({
                    'id': installation_doc.id,
                    'name': file.name,
                    'url': installation_doc.document.url if installation_doc.document else None
                })
        
        return JsonResponse({
            'success': True,
            'installation': {
                'id': installation.id,
                'customer_name': installation.customer.name,
                'item_name': installation.inventory_item.name.name if installation.inventory_item.name else 'N/A',
                'setup_date': installation.setup_date.strftime('%d.%m.%Y %H:%M'),
                'photos': uploaded_photos,
                'files': uploaded_files
            },
            'message': 'Kurulum başarıyla kaydedildi'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Geçersiz JSON formatı'
        })
    except Exception as e:
        print(f"Installation creation error: {e}")  # Debug
        return JsonResponse({
            'success': False,
            'message': 'Kurulum kaydedilirken bir hata oluştu'
        })
