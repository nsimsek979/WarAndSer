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
from .utils import get_user_accessible_companies_filter


@login_required
def warranty_tracking_list(request):
    """
    Warranty takip listesi - her ürün için en yakın garanti bitiş tarihini gösterir
    """
    # Filtreler
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset - user'ın erişebileceği şirketlere göre filtrele
    company_filter = get_user_accessible_companies_filter(request.user, 'installation')
    
    # Her installation için en yakın garanti bitiş tarihini bul
    from django.db.models import Min, Max
    
    installations_with_warranty = Installation.objects.select_related(
        'customer',
        'inventory_item__name',
        'user'
    ).prefetch_related(
        'warranty_followups'
    ).filter(company_filter).annotate(
        earliest_warranty_date=Min('warranty_followups__end_of_warranty_date'),
        latest_warranty_date=Max('warranty_followups__end_of_warranty_date')
    ).exclude(
        earliest_warranty_date__isnull=True
    ).order_by('earliest_warranty_date')
    
    # Arama filtresi
    if search_query:
        installations_with_warranty = installations_with_warranty.filter(
            Q(customer__name__icontains=search_query) |
            Q(inventory_item__name__name__icontains=search_query) |
            Q(inventory_item__serial_no__icontains=search_query)
        )
    
    # Tarih filtreleri
    now = timezone.now()
    if filter_type == 'active':
        installations_with_warranty = installations_with_warranty.filter(earliest_warranty_date__gt=now)
    elif filter_type == 'expiring_soon':
        # 30 gün içinde süresi dolacak
        thirty_days = now + timedelta(days=30)
        installations_with_warranty = installations_with_warranty.filter(
            earliest_warranty_date__gt=now,
            earliest_warranty_date__lte=thirty_days
        )
    elif filter_type == 'expired':
        installations_with_warranty = installations_with_warranty.filter(earliest_warranty_date__lte=now)
    
    # Her installation için en kritik garanti kaydını ekle
    installations = []
    for installation in installations_with_warranty:
        # En yakın tarihi olan garanti kaydını bul
        critical_warranty = installation.warranty_followups.filter(
            end_of_warranty_date=installation.earliest_warranty_date
        ).first()
        
        # Installation objesine geçici attribute ekle
        installation.critical_warranty = critical_warranty
        installations.append(installation)
    
    # Pagination
    paginator = Paginator(installations, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # İstatistikler
    stats_queryset = Installation.objects.filter(company_filter).annotate(
        earliest_warranty_date=Min('warranty_followups__end_of_warranty_date')
    ).exclude(earliest_warranty_date__isnull=True)
    
    total_items = stats_queryset.count()
    thirty_days_later = now + timedelta(days=30)
    
    # Durumları say
    active_count = stats_queryset.filter(earliest_warranty_date__gt=now).count()
    expiring_soon_count = stats_queryset.filter(
        earliest_warranty_date__gt=now,
        earliest_warranty_date__lte=thirty_days_later
    ).count()
    expired_count = stats_queryset.filter(earliest_warranty_date__lte=now).count()
    
    stats = {
        'total': total_items,
        'active': active_count,
        'expiring_soon': expiring_soon_count,
        'expired': expired_count,
    }
    
    context = {
        'installations': page_obj,  # Artık warranties yerine installations
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
    Servis takip listesi - her ürün için en yakın servis tarihini gösterir
    """
    # Filtreler
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset - user'ın erişebileceği şirketlere göre filtrele
    company_filter = get_user_accessible_companies_filter(request.user, 'installation')
    
    # Her installation için en yakın servis tarihini bul (sadece tamamlanmamış servisler)
    from django.db.models import Min, Q
    
    installations_with_service = Installation.objects.select_related(
        'customer',
        'inventory_item__name',
        'user'
    ).prefetch_related(
        'service_followups'
    ).filter(company_filter).annotate(
        next_service_date=Min('service_followups__next_service_date', 
                            filter=Q(service_followups__is_completed=False))
    ).exclude(
        next_service_date__isnull=True
    ).order_by('next_service_date')
    
    # Arama filtresi
    if search_query:
        installations_with_service = installations_with_service.filter(
            Q(customer__name__icontains=search_query) |
            Q(inventory_item__name__name__icontains=search_query) |
            Q(inventory_item__serial_no__icontains=search_query)
        )
    
    # Durum filtreleri
    now = timezone.now()
    if filter_type == 'pending':
        installations_with_service = installations_with_service.filter(next_service_date__gt=now)
    elif filter_type == 'due_soon':
        # 7 gün içinde yapılması gereken
        seven_days = now + timedelta(days=7)
        installations_with_service = installations_with_service.filter(
            next_service_date__gt=now,
            next_service_date__lte=seven_days
        )
    elif filter_type == 'overdue':
        installations_with_service = installations_with_service.filter(next_service_date__lte=now)
    elif filter_type == 'completed':
        # Tamamlanan servisler için ayrı queryset
        installations_with_service = Installation.objects.select_related(
            'customer',
            'inventory_item__name',
            'user'
        ).prefetch_related(
            'service_followups'
        ).filter(
            company_filter,
            service_followups__is_completed=True
        ).distinct().order_by('-service_followups__completed_date')
        
        if search_query:
            installations_with_service = installations_with_service.filter(
                Q(customer__name__icontains=search_query) |
                Q(inventory_item__name__name__icontains=search_query) |
                Q(inventory_item__serial_no__icontains=search_query)
            )
    
    # Her installation için en kritik servis kaydını ekle
    installations = []
    for installation in installations_with_service:
        if filter_type == 'completed':
            # En son tamamlanan servis kaydını bul
            critical_service = installation.service_followups.filter(
                is_completed=True
            ).order_by('-completed_date').first()
        else:
            # En yakın tarihi olan servis kaydını bul
            critical_service = installation.service_followups.filter(
                is_completed=False,
                next_service_date=installation.next_service_date
            ).first()
        
        # Installation objesine geçici attribute ekle
        installation.critical_service = critical_service
        installations.append(installation)
    
    # Pagination
    paginator = Paginator(installations, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # İstatistikler
    stats_queryset = Installation.objects.filter(company_filter).annotate(
        next_service_date=Min('service_followups__next_service_date', 
                            filter=Q(service_followups__is_completed=False))
    ).exclude(next_service_date__isnull=True)
    
    total_items = stats_queryset.count()
    seven_days_later = now + timedelta(days=7)
    
    # Durumları say
    pending_count = stats_queryset.filter(next_service_date__gt=now).count()
    due_soon_count = stats_queryset.filter(
        next_service_date__gt=now,
        next_service_date__lte=seven_days_later
    ).count()
    overdue_count = stats_queryset.filter(next_service_date__lte=now).count()
    
    # Tamamlanan servisleri say
    completed_count = Installation.objects.filter(
        company_filter,
        service_followups__is_completed=True
    ).distinct().count()
    
    stats = {
        'total': total_items,
        'pending': pending_count,
        'due_soon': due_soon_count,
        'overdue': overdue_count,
        'completed': completed_count,
    }
    
    context = {
        'installations': page_obj,  # Artık services yerine installations
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
        from django.utils import timezone
        
        # Queryset'i oluştur - user'ın erişebileceği şirketlere göre filtrele
        company_filter = get_user_accessible_companies_filter(self.request.user, 'installation')
        queryset = Installation.objects.select_related(
            'customer',
            'inventory_item__name'
        ).prefetch_related(
            'warranty_followups',
            'service_followups'
        ).annotate(
            next_warranty_end=Min('warranty_followups__end_of_warranty_date'),
            next_service_date=Min('service_followups__next_service_date')
        ).filter(company_filter).order_by('-setup_date')
        
        # Filtre parametresi kontrolü
        filter_type = self.request.GET.get('filter')
        if filter_type == 'active_warranty':
            # Sadece garanti süresi devam eden kurulumlar
            now = timezone.now()
            queryset = queryset.filter(
                warranty_followups__end_of_warranty_date__gt=now
            ).distinct()
        
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
        context['filter_type'] = self.request.GET.get('filter', '')
        return context


# Mobile Views
@login_required
def mobile_main(request):
    """
    Mobil ana sayfa
    """
    
    # Kullanıcının erişebileceği şirketleri al
    from .utils import get_user_accessible_companies_filter
    company_filter = get_user_accessible_companies_filter(request.user, 'installation')
    
    # Bugünkü işler - kurulum + bakım
    from django.utils import timezone
    from datetime import date
    
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    # Bugün yapılan kurulumlar
    todays_installations = Installation.objects.filter(
        company_filter,
        setup_date__date=today
    ).count()
    
    # Bugün yapılan bakım/servis işleri (buraya service modeli geldiğinde eklenecek)
    todays_services = 0  # Service.objects.filter(...).count()
    
    todays_work = todays_installations + todays_services
    
    # Bu ay yapılan işler
    monthly_installations = Installation.objects.filter(
        company_filter,
        setup_date__date__gte=start_of_month
    ).count()
    
    monthly_services = 0  # Service.objects.filter(...).count()
    monthly_work = monthly_installations + monthly_services
    
    context = {
        'todays_work': todays_work,
        'monthly_work': monthly_work,
    }
    
    return render(request, 'warranty_and_services/mobile/mobile_main.html', context)


@login_required
def mobile_maintenance_scanner(request):
    """
    Mobil bakım scanner sayfası
    """
    
    return render(request, 'warranty_and_services/mobile/maintenance_scanner.html')


@login_required  
def mobile_maintenance_form(request):
    """
    Mobile maintenance form page
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get installation data from session or URL parameter
    installation_id = request.GET.get('installation_id') or request.session.get('maintenance_installation_id')
    
    if not installation_id:
        messages.error(request, 'Kurulum bilgisi bulunamadı')
        return redirect('warranty_and_services:mobile_maintenance_scanner')
    
    try:
        installation = get_object_or_404(Installation, id=installation_id)
        
        # Get warranty and service information
        warranties = installation.warranty_followups.all().order_by('end_of_warranty_date')
        services = installation.service_followups.all().order_by('-next_service_date')
        
        # Last maintenance date
        last_maintenance = services.filter(is_completed=True).first()
        last_maintenance_date = last_maintenance.completed_date.strftime('%d.%m.%Y') if last_maintenance and last_maintenance.completed_date else 'Henüz bakım yapılmamış'
        
        context = {
            'installation': {
                'id': installation.id,
                'item_name': installation.inventory_item.name.name if installation.inventory_item.name else 'N/A',
                'item_shortcode': installation.inventory_item.name.shortcode if installation.inventory_item.name else 'N/A',
                'serial_no': installation.inventory_item.serial_no,
                'customer_name': installation.customer.name,
                'installation_date': installation.setup_date.strftime('%d.%m.%Y'),
                'installation_location': installation.location_address or 'Konum belirtilmemiş',
                'last_maintenance_date': last_maintenance_date
            },
            'warranties': warranties,
            'services': services
        }
        
        return render(request, 'warranty_and_services/mobile/maintenance_form.html', context)
        
    except Installation.DoesNotExist:
        messages.error(request, 'Kurulum bulunamadı')
        return redirect('warranty_and_services:mobile_maintenance_scanner')


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
        
        # QR code formatı: "ID:{id}|CODE:{serial}|NAME:{name}|SERIAL:{serial}"
        # QR string'ini parse et
        inventory_item = None
        
        if 'ID:' in qr_code and '|' in qr_code:
            # QR kod formatını parse et
            parts = qr_code.split('|')
            id_part = [part for part in parts if part.startswith('ID:')]
            if id_part:
                item_id = id_part[0].replace('ID:', '')
                inventory_item = InventoryItem.objects.select_related('name', 'name__brand_name', 'name__category').filter(
                    id=item_id, in_used=False
                ).first()
            else:
                # ID bulunamadı, serial ile dene
                serial_part = [part for part in parts if part.startswith('SERIAL:')]
                if serial_part:
                    serial_no = serial_part[0].replace('SERIAL:', '')
                    inventory_item = InventoryItem.objects.select_related('name', 'name__brand_name', 'name__category').filter(
                        serial_no=serial_no, in_used=False
                    ).first()
        else:
            # QR formatı farklı, direkt serial number olarak dene
            inventory_item = InventoryItem.objects.select_related('name', 'name__brand_name', 'name__category').filter(
                serial_no=qr_code, in_used=False
            ).first()
            if not inventory_item:
                return JsonResponse({
                    'success': False,
                    'message': 'Bu QR kodu ile eşleşen kuruluma hazır ürün bulunamadı'
                })
            
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
        
        inventory_item = InventoryItem.objects.select_related('name', 'name__brand_name', 'name__category').filter(
            serial_no=serial_number, in_used=False
        ).first()
        
        if not inventory_item:
            return JsonResponse({
                'success': False,
                'message': 'Bu seri numarası ile eşleşen kuruluma hazır ürün bulunamadı'
            })
        
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
        
        # Get user's accessible companies using utility function
        from .utils import get_user_accessible_companies
        accessible_company_ids = get_user_accessible_companies(user)
        
        if not accessible_company_ids:
            return JsonResponse({
                'success': False,
                'message': 'Kullanıcının erişebileceği firma bulunamadı'
            })
        
        print(f"User company: {user_company.name if user_company else 'None'}")
        print(f"Searching in company hierarchy: {accessible_company_ids}")
        
        # Search customers within the accessible companies
        customers = Company.objects.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(tax_number__icontains=search_query),
            id__in=accessible_company_ids,
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


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_customer_create(request):
    """Customer creation API endpoint"""
    print(f"Customer create API called by user: {request.user}")
    print(f"Request method: {request.method}")
    print(f"Request content type: {request.content_type}")
    
    try:
        data = json.loads(request.body)
        print(f"Received data: {data}")
        
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
        
        # Create working hours if provided
        daily_working_hours = data.get('daily_working_hours', 8)
        working_on_saturday = data.get('working_on_saturday', False)
        working_on_sunday = data.get('working_on_sunday', False)
        
        from customer.models import WorkingHours
        WorkingHours.objects.create(
            customer=customer,
            daily_working_hours=daily_working_hours,
            working_on_saturday=working_on_saturday,
            working_on_sunday=working_on_sunday
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
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Geçersiz JSON formatı'
        })
    except Exception as e:
        print(f"Customer creation error: {e}")  # Debug
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Müşteri oluşturulurken bir hata oluştu: {str(e)}'
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_installation_create(request):
    """Installation creation API endpoint with file uploads"""
    print(f"Installation create API called by user: {request.user}")
    print(f"Request method: {request.method}")
    
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
            location_latitude=data.get('latitude'),  # Fixed field name
            location_longitude=data.get('longitude'),  # Fixed field name
            location_address=data.get('setup_location', '').strip(),  # Fixed field name
            installation_notes=data.get('installation_notes', '').strip()
        )
        
        # Mark item as in use
        item.in_used = True
        item.save()
        
        # Handle file uploads
        uploaded_photos = []
        uploaded_files = []
        
        # Handle photos - check for individual photo fields (photo_0, photo_1, etc.)
        photo_index = 0
        while f'photo_{photo_index}' in request.FILES:
            photo = request.FILES[f'photo_{photo_index}']
            
            # Validate photo
            if photo.content_type.startswith('image/') and photo.size <= 5 * 1024 * 1024:  # 5MB limit
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
            
            photo_index += 1
        
        # Also handle legacy 'photos' field if exists
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

        # Handle files/documents - check for individual file fields (file_0, file_1, etc.)
        file_index = 0
        while f'file_{file_index}' in request.FILES:
            file = request.FILES[f'file_{file_index}']
            
            # Validate file
            if file.size <= 10 * 1024 * 1024:  # 10MB limit
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
            
            file_index += 1
        
        # Also handle legacy 'files' field if exists
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


# Maintenance API Endpoints
@csrf_exempt
@require_http_methods(["POST"])
def api_installation_search_by_qr(request):
    """
    QR kod ile kurulmuş ürün arama API endpoint'i
    """
    try:
        data = json.loads(request.body)
        qr_code = data.get('qr_code', '').strip()
        
        if not qr_code:
            return JsonResponse({
                'success': False,
                'message': 'QR kodu gerekli'
            })
        
        # QR kod formatını parse et ve item'ı bul
        from item_master.models import InventoryItem
        try:
            inventory_item = None
            
            if 'ID:' in qr_code and '|' in qr_code:
                # QR kod formatını parse et
                parts = qr_code.split('|')
                id_part = [part for part in parts if part.startswith('ID:')]
                if id_part:
                    item_id = id_part[0].replace('ID:', '')
                    inventory_item = InventoryItem.objects.get(id=item_id)
            else:
                # Direkt serial number olarak dene
                inventory_item = InventoryItem.objects.get(serial_no=qr_code)
            
            if not inventory_item:
                raise InventoryItem.DoesNotExist
            
            # Bu item'ın kurulumunu bul - user'ın erişebileceği şirketlere göre filtrele
            company_filter = get_user_accessible_companies_filter(request.user, 'installation')
            installation_query = Installation.objects.select_related(
                'customer',
                'inventory_item__name'
            ).filter(inventory_item=inventory_item).filter(company_filter)
            
            installation = installation_query.first()
            
            if not installation:
                return JsonResponse({
                    'success': False,
                    'message': 'Bu QR kodu ile erişiminizde olan kurulmuş ürün bulunamadı'
                })
            
            # Installation bilgilerini dön
            return JsonResponse({
                'success': True,
                'installation': {
                    'id': installation.id,
                    'customer_name': installation.customer.name,
                    'item_name': installation.inventory_item.name.name if installation.inventory_item.name else 'N/A',
                    'serial_number': installation.inventory_item.serial_no or 'N/A',
                    'setup_date': installation.setup_date.strftime('%d.%m.%Y'),
                    'location_address': installation.location_address or '',
                }
            })
            
        except (InventoryItem.DoesNotExist, Installation.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'Bu QR kodu ile kurulmuş ürün bulunamadı'
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
def api_installation_search_by_serial(request):
    """
    Seri numarası ile kurulmuş ürün arama API endpoint'i
    """
    try:
        data = json.loads(request.body)
        serial_number = data.get('serial_number', '').strip()
        customer_filter = data.get('customer_filter', '').strip()
        
        if not serial_number:
            return JsonResponse({
                'success': False,
                'message': 'Seri numarası gerekli'
            })
        
        # Seri numarası ile item'ı bul
        from item_master.models import InventoryItem
        try:
            inventory_item = InventoryItem.objects.get(serial_no=serial_number)
            
            # Bu item'ın kurulumunu bul - user'ın erişebileceği şirketlere göre filtrele
            company_filter = get_user_accessible_companies_filter(request.user, 'installation')
            installation_query = Installation.objects.select_related(
                'customer',
                'inventory_item__name'
            ).filter(inventory_item=inventory_item).filter(company_filter)
            
            # Müşteri filtresi varsa uygula
            if customer_filter:
                installation_query = installation_query.filter(
                    customer__name__icontains=customer_filter
                )
            
            installation = installation_query.first()
            
            if not installation:
                message = 'Bu seri numarası ile erişiminizde olan kurulmuş ürün bulunamadı'
                if customer_filter:
                    message += f' (Müşteri filtresi: {customer_filter})'
                return JsonResponse({
                    'success': False,
                    'message': message
                })
            
            # Installation bilgilerini dön
            return JsonResponse({
                'success': True,
                'installation': {
                    'id': installation.id,
                    'customer_name': installation.customer.name,
                    'item_name': installation.inventory_item.name.name if installation.inventory_item.name else 'N/A',
                    'serial_number': installation.inventory_item.serial_no or 'N/A',
                    'setup_date': installation.setup_date.strftime('%d.%m.%Y'),
                    'location_address': installation.location_address or '',
                }
            })
            
        except InventoryItem.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Bu seri numarası ile ürün bulunamadı'
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
def api_maintenance_create(request):
    """
    Maintenance kaydı oluşturma API endpoint'i
    """
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
        if not data.get('installation_id'):
            return JsonResponse({
                'success': False,
                'message': 'Kurulum ID gereklidir'
            })
        
        if not data.get('maintenance_date'):
            return JsonResponse({
                'success': False,
                'message': 'Bakım tarihi gereklidir'
            })
        
        try:
            installation = Installation.objects.get(id=data['installation_id'])
        except Installation.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Kurulum bulunamadı'
            })
        
        # Parse maintenance date
        try:
            maintenance_date = datetime.fromisoformat(data['maintenance_date'].replace('Z', '+00:00'))
            # Make timezone aware if it's naive
            if maintenance_date.tzinfo is None:
                maintenance_date = timezone.make_aware(maintenance_date)
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Geçersiz tarih formatı'
            })
        
        # Check if maintenance date is in the future
        current_time = timezone.now()
        if maintenance_date > current_time:
            return JsonResponse({
                'success': False,
                'message': 'Bakım tarihi bugünden ileri olamaz'
            })
        
        # Create maintenance record (we'll create a Maintenance model later)
        # For now, we'll store it as a service followup
        service_followup = ServiceFollowUp.objects.create(
            installation=installation,
            service_type='maintenance',  # Yeni tip ekleyeceğiz
            service_value=1,  # Dummy value
            next_service_date=maintenance_date,
            is_completed=True,
            completion_date=maintenance_date,
            completion_notes=data.get('maintenance_notes', '').strip(),
            calculation_notes=f"Bakım/Onarım - {data.get('maintenance_type', 'Genel Bakım')}"
        )
        
        # Handle file uploads (photos, documents)
        uploaded_photos = []
        uploaded_files = []
        
        # Handle photos
        if 'photos' in request.FILES:
            photos = request.FILES.getlist('photos')
            for photo in photos:
                if not photo.content_type.startswith('image/'):
                    continue
                if photo.size > 5 * 1024 * 1024:  # 5MB limit
                    continue
                    
                installation_image = InstallationImage.objects.create(
                    installation=installation,
                    image=photo,
                    description=f"Bakım fotoğrafı - {photo.name}",
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
                if file.size > 10 * 1024 * 1024:  # 10MB limit
                    continue
                    
                installation_doc = InstallationDocument.objects.create(
                    installation=installation,
                    document=file,
                    description=f"Bakım dökümanı - {file.name}",
                    uploaded_by=request.user
                )
                uploaded_files.append({
                    'id': installation_doc.id,
                    'name': file.name,
                    'url': installation_doc.document.url if installation_doc.document else None
                })
        
        return JsonResponse({
            'success': True,
            'maintenance': {
                'id': service_followup.id,
                'installation_id': installation.id,
                'customer_name': installation.customer.name,
                'item_name': installation.inventory_item.name.name if installation.inventory_item.name else 'N/A',
                'maintenance_date': maintenance_date.strftime('%d.%m.%Y %H:%M'),
                'photos': uploaded_photos,
                'files': uploaded_files
            },
            'message': 'Bakım kaydı başarıyla oluşturuldu'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Geçersiz JSON formatı'
        })
    except Exception as e:
        print(f"Maintenance creation error: {e}")  # Debug
        return JsonResponse({
            'success': False,
            'message': 'Bakım kaydı oluşturulurken bir hata oluştu'
        })


# Mobile Views
@login_required
def mobile_installation_scanner(request):
    """Mobile Installation Scanner sayfası"""
    return render(request, 'warranty_and_services/mobile/mobile_installation_scanner.html')


@login_required
def mobile_maintenance_scanner(request):
    """Mobile Maintenance Scanner sayfası"""
    return render(request, 'warranty_and_services/mobile/mobile_maintenance_scanner.html')


# Maintenance API endpoints
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_maintenance_search(request):
    """
    Bakım için kurulumu yapılmış (in_used=True) itemları ara
    """
    try:
        data = json.loads(request.body)
        search_term = data.get('search_term', '').strip()
        
        if not search_term:
            return JsonResponse({
                'success': False,
                'message': 'Arama terimi gerekli'
            })
        
        # Kurulumu yapılmış itemları ara (in_used=True olan)
        from item_master.models import InventoryItem
        
        installed_items = InventoryItem.objects.filter(
            in_used=True  # Sadece kurulumu yapılmış itemlar
        ).filter(
            Q(serial_no__icontains=search_term) |
            Q(name__name__icontains=search_term) |
            Q(name__shortcode__icontains=search_term)
        ).select_related('name').prefetch_related('installation_set__customer')
        
        if not installed_items.exists():
            return JsonResponse({
                'success': False,
                'message': 'Bu arama terimine uygun kurulumu yapılmış ekipman bulunamadı'
            })
        
        results = []
        for item in installed_items:
            # Bu item'in kurulum bilgilerini al
            installation = Installation.objects.filter(
                inventory_item=item
            ).select_related('customer').first()
            
            if installation:
                results.append({
                    'inventory_item_id': item.id,
                    'installation_id': installation.id,
                    'serial_no': item.serial_no,
                    'item_name': item.name.name if item.name else 'N/A',
                    'item_shortcode': item.name.shortcode if item.name else 'N/A',
                    'customer_name': installation.customer.name,
                    'installation_date': installation.setup_date.strftime('%d.%m.%Y'),
                    'installation_location': installation.location_address or 'Konum belirtilmemiş',
                    'has_location': installation.has_location
                })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Geçersiz JSON formatı'
        })
    except Exception as e:
        print(f"Maintenance search error: {e}")  # Debug
        return JsonResponse({
            'success': False,
            'message': 'Arama sırasında bir hata oluştu'
        })


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_maintenance_item_detail(request):
    """
    Seçilen kurulumu yapılmış item'in detaylarını ve servis geçmişini getir
    """
    try:
        data = json.loads(request.body)
        installation_id = data.get('installation_id')
        
        if not installation_id:
            return JsonResponse({
                'success': False,
                'message': 'Kurulum ID gerekli'
            })
        
        installation = get_object_or_404(Installation, id=installation_id)
        
        # Garanti bilgileri
        warranties = installation.warranty_followups.all().order_by('end_of_warranty_date')
        warranty_info = []
        for warranty in warranties:
            warranty_info.append({
                'type': warranty.get_warranty_type_display(),
                'value': warranty.warranty_value,
                'end_date': warranty.end_of_warranty_date.strftime('%d.%m.%Y'),
                'is_active': warranty.is_active,
                'days_remaining': warranty.days_remaining
            })
        
        # Servis geçmişi
        service_history = installation.service_followups.all().order_by('-next_service_date')
        service_info = []
        for service in service_history:
            service_info.append({
                'id': service.id,
                'type': service.get_service_type_display(),
                'value': service.service_value,
                'next_date': service.next_service_date.strftime('%d.%m.%Y'),
                'is_completed': service.is_completed,
                'is_due': service.is_due,
                'completion_notes': service.completion_notes
            })
        
        # Son bakım tarihi
        last_maintenance = service_history.filter(is_completed=True).first()
        last_maintenance_date = last_maintenance.completed_date.strftime('%d.%m.%Y') if last_maintenance and last_maintenance.completed_date else 'Henüz bakım yapılmamış'
        
        return JsonResponse({
            'success': True,
            'installation': {
                'id': installation.id,
                'customer_name': installation.customer.name,
                'customer_phone': installation.customer.telephone or 'Belirtilmemiş',
                'customer_email': installation.customer.email or 'Belirtilmemiş',
                'item_name': installation.inventory_item.name.name if installation.inventory_item.name else 'N/A',
                'item_shortcode': installation.inventory_item.name.shortcode if installation.inventory_item.name else 'N/A',
                'serial_no': installation.inventory_item.serial_no,
                'installation_date': installation.setup_date.strftime('%d.%m.%Y'),
                'installation_location': installation.location_address or 'Konum belirtilmemiş',
                'has_location': installation.has_location,
                'location_coordinates': {
                    'latitude': float(installation.location_latitude) if installation.location_latitude else None,
                    'longitude': float(installation.location_longitude) if installation.location_longitude else None
                } if installation.has_location else None,
                'last_maintenance_date': last_maintenance_date
            },
            'warranties': warranty_info,
            'service_history': service_info
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Geçersiz JSON formatı'
        })
    except Exception as e:
        print(f"Maintenance detail error: {e}")  # Debug
        return JsonResponse({
            'success': False,
            'message': 'Detay bilgileri alınırken bir hata oluştu'
        })


@login_required
@require_http_methods(["POST"])
def api_maintenance_submit(request):
    """
    Bakım kaydı oluştur - Yeni MaintenanceRecord modeli ile
    """
    try:
        installation_id = request.POST.get('installation_id')
        
        if not installation_id:
            return JsonResponse({
                'success': False,
                'message': 'Kurulum ID gerekli'
            })
        
        installation = get_object_or_404(Installation, id=installation_id)
        
        # Get form data
        maintenance_type = request.POST.get('maintenance_type')
        breakdown_reason = request.POST.get('breakdown_reason', '')
        notes = request.POST.get('work_performed', '')
        service_date = request.POST.get('service_date')
        
        # Validate required fields
        if not maintenance_type:
            return JsonResponse({
                'success': False,
                'message': 'Bakım türü seçimi zorunludur'
            })
        
        if not service_date:
            return JsonResponse({
                'success': False,
                'message': 'Bakım tarihi zorunludur'
            })
        
        if maintenance_type == 'breakdown' and not breakdown_reason:
            return JsonResponse({
                'success': False,
                'message': 'Arıza bakımı için arıza sebebi zorunludur'
            })
        
        # Find an existing incomplete service follow-up or create one
        service_followup = ServiceFollowUp.objects.filter(
            installation=installation,
            is_completed=False
        ).first()
        
        if not service_followup:
            # Create a new service follow-up
            from datetime import timedelta
            next_service_date = timezone.now() + timedelta(days=180)  # 6 months default
            
            service_followup = ServiceFollowUp.objects.create(
                installation=installation,
                service_type='time_term',
                service_value=6,  # 6 months
                next_service_date=next_service_date,
                calculation_notes='Created automatically for maintenance record'
            )
        
        # Import the new models
        from .models import MaintenanceRecord, MaintenancePhoto, MaintenanceDocument
        
        # Create MaintenanceRecord
        maintenance_record = MaintenanceRecord.objects.create(
            service_followup=service_followup,
            maintenance_type=maintenance_type,
            technician=request.user,
            breakdown_reason=breakdown_reason,
            notes=notes,
            service_date=service_date
        )
        
        # Handle multiple photos
        for key, file in request.FILES.items():
            if key.startswith('photo_'):
                MaintenancePhoto.objects.create(
                    maintenance_record=maintenance_record,
                    image=file,
                    description=f'Bakım fotoğrafı'
                )
            elif key.startswith('document_'):
                MaintenanceDocument.objects.create(
                    maintenance_record=maintenance_record,
                    document=file,
                    name=file.name,
                    description=f'Bakım belgesi'
                )

        # Handle service forms
        completed_service_forms = request.POST.get('completed_service_forms', '[]')
        try:
            import json
            completed_forms = json.loads(completed_service_forms)
            from .models import MaintenanceServiceForm
            
            for form_id in completed_forms:
                try:
                    service_form = installation.inventory_item.name.service_forms.get(id=form_id)
                    MaintenanceServiceForm.objects.create(
                        maintenance_record=maintenance_record,
                        service_form=service_form,
                        is_completed=True
                    )
                except:
                    pass  # Skip if service form not found
        except:
            pass

        # Handle spare parts
        used_spare_parts = request.POST.get('used_spare_parts', '[]')
        try:
            used_parts = json.loads(used_spare_parts)
            from .models import MaintenanceSparePart
            
            for part_data in used_parts:
                try:
                    spare_part = installation.inventory_item.name.spare_parts.get(id=part_data['id'])
                    MaintenanceSparePart.objects.create(
                        maintenance_record=maintenance_record,
                        spare_part=spare_part,
                        is_used=True,
                        quantity_used=part_data.get('quantity', 1)
                    )
                except:
                    pass  # Skip if spare part not found
        except:
            pass
        
        # Mark service follow-up as completed
        service_followup.is_completed = True
        service_followup.completed_date = timezone.now()
        service_followup.completion_notes = f"Maintenance completed - {maintenance_type}"
        service_followup.save()
        
        # Send notification email
        try:
            maintenance_record.send_maintenance_notification()
            print(f"✅ Email notification sent successfully for maintenance ID: {maintenance_record.id}")
        except Exception as e:
            print(f"❌ Email notification failed: {e}")
            import traceback
            traceback.print_exc()
        
        return JsonResponse({
            'success': True,
            'message': 'Bakım kaydı başarıyla oluşturuldu',
            'maintenance_id': maintenance_record.id
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': f'Geçersiz veri formatı: {str(e)}'
        })
    except Exception as e:
        print(f"Maintenance submit error: {e}")  # Debug
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Bakım kaydı oluşturulurken bir hata oluştu: {str(e)}'
        })


@login_required
def api_installation_service_forms(request, installation_id):
    """
    Installation için service form'ları getir
    """
    try:
        installation = get_object_or_404(Installation, id=installation_id)
        service_forms = installation.inventory_item.name.service_forms.all()
        
        forms_data = []
        for form in service_forms:
            forms_data.append({
                'id': form.id,
                'name': form.name,
                'description': getattr(form, 'description', ''),
            })
        
        return JsonResponse(forms_data, safe=False)
        
    except Exception as e:
        print(f"Service forms API error: {e}")
        return JsonResponse([], safe=False)


@login_required  
def api_installation_spare_parts(request, installation_id):
    """
    Installation için spare parts'ları getir
    """
    try:
        installation = get_object_or_404(Installation, id=installation_id)
        spare_parts = installation.inventory_item.name.spare_parts.all()
        
        parts_data = []
        for part in spare_parts:
            parts_data.append({
                'id': part.id,
                'name': part.name,
                'description': getattr(part, 'description', ''),
            })
        
        return JsonResponse(parts_data, safe=False)
        
    except Exception as e:
        print(f"Spare parts API error: {e}")
        return JsonResponse([], safe=False)


@login_required
def item_service_history(request, installation_id):
    """
    Item bazlı service history detail sayfası - o item'a yapılan tüm maintenance kayıtları
    """
    try:
        installation = get_object_or_404(Installation, id=installation_id)
        
        # User permissions check
        company_filter = get_user_accessible_companies_filter(request.user, 'installation')
        if not Installation.objects.filter(id=installation_id).filter(company_filter).exists():
            messages.error(request, 'Bu kuruluma erişim yetkiniz yok.')
            return redirect('warranty_and_services:service_tracking_list')
        
        # Get all maintenance records for this installation (directly from MaintenanceRecord)
        from .models import MaintenanceRecord
        
        all_maintenance_records = MaintenanceRecord.objects.filter(
            service_followup__installation=installation
        ).prefetch_related(
            'spare_parts__spare_part',
            'service_forms__service_form',
            'photos',
            'documents',
            'technician',
            'service_followup'
        ).order_by('-created_at')
        
        # Sort by service date (most recent first)
        all_maintenance_records = list(all_maintenance_records)
        all_maintenance_records.sort(key=lambda x: x.service_date if isinstance(x.service_date, str) else x.service_date.strftime('%Y-%m-%d'), reverse=True)
        
        # Get current active service follow-ups
        active_services = installation.service_followups.filter(
            is_completed=False
        ).order_by('next_service_date')
        
        # Statistics
        total_maintenances = len(all_maintenance_records)
        periodic_count = len([m for m in all_maintenance_records if m.maintenance_type == 'periodic'])
        breakdown_count = len([m for m in all_maintenance_records if m.maintenance_type == 'breakdown'])
        
        # Last maintenance date
        last_maintenance = all_maintenance_records[0] if all_maintenance_records else None
        
        context = {
            'installation': installation,
            'customer': installation.customer,
            'inventory_item': installation.inventory_item,
            'maintenance_records': all_maintenance_records,
            'active_services': active_services,
            'total_maintenances': total_maintenances,
            'periodic_count': periodic_count,
            'breakdown_count': breakdown_count,
            'last_maintenance': last_maintenance,
            'warranties': installation.warranty_followups.all().order_by('end_of_warranty_date'),
        }
        
        return render(request, 'warranty_and_services/item_service_history.html', context)
        
    except Installation.DoesNotExist:
        messages.error(request, 'Kurulum bulunamadı.')
        return redirect('warranty_and_services:service_tracking_list')
    except Exception as e:
        messages.error(request, f'Bir hata oluştu: {str(e)}')
        return redirect('warranty_and_services:service_tracking_list')
7

def installation_map_view(request):
    """
    Display installations on a Google Map
    """
    print("=== MAP VIEW DEBUG ===")
    try:
        # Get all installations with location data
        installations = Installation.objects.filter(
            location_latitude__isnull=False,
            location_longitude__isnull=False
        ).select_related('customer', 'inventory_item', 'inventory_item__name')
        
        print(f"Found {installations.count()} installations with coordinates")
        
        markers = []
        for installation in installations:
            print(f"Processing installation: {installation.id} - {installation.inventory_item}")
            
            # Get next service date
            next_service = "Belirtilmemiş"
            services = installation.service_followups.filter(is_completed=False).order_by('next_service_date')
            if services.exists():
                next_service = services.first().next_service_date.strftime('%d.%m.%Y')
            
            # Determine marker color based on service status
            color = '#10B981'  # Green default
            if services.exists():
                service = services.first()
                next_service_date = service.next_service_date
                # Ensure both are date objects for subtraction
                if hasattr(next_service_date, 'date'):
                    next_service_date = next_service_date.date()
                days_until = (next_service_date - timezone.now().date()).days
                if days_until < 0:
                    color = '#EF4444'  # Red - overdue
                elif days_until <= 7:
                    color = '#F59E0B'  # Yellow - due soon
            
            markers.append({
                'lat': float(installation.location_latitude),
                'lng': float(installation.location_longitude),
                'title': installation.inventory_item.name.name if installation.inventory_item.name else 'Ürün',
                'customer': installation.customer.name,
                'address': installation.location_address or 'Adres belirtilmemiş',
                'dealer': installation.customer.related_company.name if installation.customer.related_company else 'Bayi belirtilmemiş',
                'next_service': next_service,
                'installation_id': installation.id,
                'color': color
            })
        
        print(f"Created {len(markers)} markers")
        
        # Convert to JSON for JavaScript
        markers_json = json.dumps(markers)
        
        context = {
            'markers_json': markers_json,
            'total_installations': len(markers)
        }
        
        print("Rendering template...")
        return render(request, 'warranty_and_services/installation_map.html', context)
        
    except Exception as e:
        print(f"ERROR in map view: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Harita yüklenirken hata oluştu: {str(e)}')
        return redirect('warranty_and_services:installation_list')
