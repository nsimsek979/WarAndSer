from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.translation import gettext as _
from .models import Company, City, Country, County, District, CoreBusiness, WorkingHours
from custom_user.permissions import get_company_queryset_for_user
from django.db import models
from django.core.paginator import Paginator


@login_required(login_url='login')
def api_managers(request):
	# Only fetch users with roles manager_main and salesmanager_main
	User = get_user_model()
	managers = User.objects.filter(role__in=['manager_main', 'salesmanager_main']).values('id', 'first_name', 'last_name', 'email')
	data = [
		{
			'id': m['id'],
			'full_name': f"{m['first_name']} {m['last_name']}".strip() or m['email']
		}
		for m in managers
	]
	return JsonResponse(data, safe=False)

@login_required(login_url='login')
def customer_detail(request, pk):
	from django.db.models import Min
	from django.core.paginator import Paginator
	company = get_object_or_404(Company, pk=pk)
	
	# Check if user can view this customer (use same permission as edit for now)
	if not can_user_edit_customer(request.user, company):
		# For view, we use a more permissive check - can see if in their queryset
		user_companies = get_company_queryset_for_user(request.user)
		if not user_companies.filter(id=company.id).exists():
			from django.core.exceptions import PermissionDenied
			raise PermissionDenied("You don't have permission to view this customer.")
	
	# Get installations for this customer
	from warranty_and_services.models import Installation
	
	# Base installations for this company
	installations = Installation.objects.filter(customer=company)
	
	# If this company is a distributor, also include installations from related end users
	if company.company_type.lower() == 'distributor':
		related_endusers = Company.objects.filter(related_company=company)
		installations = Installation.objects.filter(
			models.Q(customer=company) | models.Q(customer__in=related_endusers)
		)
	
	installations = installations.select_related(
		'inventory_item__name',
		'customer'
	).prefetch_related(
		'warranty_followups',
		'service_followups'
	).annotate(
		next_warranty_end=Min('warranty_followups__end_of_warranty_date'),
		next_service_date=Min('service_followups__next_service_date')
	).order_by('-setup_date')
	
	# Get service tracking records for this customer
	from warranty_and_services.models import ServiceFollowUp
	
	# Filtreleme mantığını düzelt:
	# 1. Eğer görüntülenen company bir distributor ise, hem kendisinin hem de related_company olarak onu gören enduser'ların service'lerini göster
	# 2. Eğer görüntülenen company bir enduser ise, sadece o company'nin service'lerini göster
	
	if company.company_type.lower() == 'distributor':
		# Distributor case: kendi service'leri + related enduser'ların service'leri
		related_endusers = Company.objects.filter(related_company=company)
		service_trackings = ServiceFollowUp.objects.filter(
			models.Q(installation__customer=company) | 
			models.Q(installation__customer__in=related_endusers)
		)
	else:
		# Enduser case: sadece o company'nin service'leri
		service_trackings = ServiceFollowUp.objects.filter(installation__customer=company)
	
	service_trackings = service_trackings.select_related(
		'installation__customer',
		'installation',
		'installation__inventory_item__name',
		'installation__user'
	)
	
	# Convert to list and sort by status priority (overdue, due soon, pending, done)
	service_trackings = list(service_trackings)
	service_trackings.sort(key=lambda x: (x.service_status_priority, x.next_service_date))
	service_trackings = service_trackings[:20]  # Latest 20 service records
	
	# Get warranty tracking records for this customer
	from warranty_and_services.models import WarrantyFollowUp
	
	# Base warranty trackings for this company
	warranty_trackings = WarrantyFollowUp.objects.filter(installation__customer=company)
	
	# If this company is a distributor, also include warranty trackings from related end users
	if company.company_type.lower() == 'distributor':
		related_endusers = Company.objects.filter(related_company=company)
		warranty_trackings = WarrantyFollowUp.objects.filter(
			models.Q(installation__customer=company) | 
			models.Q(installation__customer__in=related_endusers)
		)
	
	warranty_trackings = warranty_trackings.select_related(
		'installation__customer',
		'installation',
		'installation__inventory_item__name'
	).order_by('-end_of_warranty_date')[:20]  # Latest 20 warranty records
	
	# Pagination for installations
	paginator = Paginator(installations, 10)  # 10 installations per page
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	
	context = {
		'company': company,
		'installations': page_obj,
		'service_trackings': service_trackings,
		'warranty_trackings': warranty_trackings,
		'page_obj': page_obj,
		'is_paginated': page_obj.has_other_pages(),
	}
	return render(request, 'pages/customer/customer-detail.html', context)



@login_required(login_url='login')
def customer_list(request):
	search_query = request.GET.get('search', '').strip()
	page_number = request.GET.get('page', 1)
	user = request.user
	company_qs = get_company_queryset_for_user(user, Company.objects.select_related('core_business').prefetch_related('address__city').all())
	if search_query:
		company_qs = company_qs.filter(
			models.Q(name__icontains=search_query) |
			models.Q(core_business__name__icontains=search_query) |
			models.Q(address__city__name__icontains=search_query)
		).distinct()
	paginator = Paginator(company_qs, 20)
	page_obj = paginator.get_page(page_number)
	context = {
		'title': _('Customer List'),
		'page_obj': page_obj,
		'is_paginated': page_obj.has_other_pages(),
		'search_query': search_query,
		'items': page_obj.object_list,
	}
	return render(request, 'pages/customer/customer-list.html', context)


# --- Create Customer View and API Endpoints ---
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.db import transaction
from .models import ContactPerson, Address, WorkingHours

@login_required(login_url='login')
@permission_required('customer.add_company', raise_exception=True)
def customer_create(request):
	if request.method == 'POST':
		try:
			with transaction.atomic():
				# Determine related_company based on user role
				related_company_id = request.POST.get('related_company') or None
				company_type = request.POST.get('company_type')
				related_manager_id = request.POST.get('related_manager') or None
				user = request.user
				
				# If user is distributor_manager or service, auto-set their distributor as related company
				if user.role in ['manager_distributor', 'salesmanager_distributor', 'service_distributor'] and user.company:
					related_company_id = user.company.id
					company_type = 'enduser'  # Auto-set to End User
					# Set related manager to the distributor's related manager
					if user.company.related_manager:
						related_manager_id = user.company.related_manager.id
				
				# Create the company
				company = Company.objects.create(
					name=request.POST.get('name'),
					company_type=company_type,
					core_business_id=request.POST.get('core_business') or None,
					related_company_id=related_company_id,
					related_manager_id=related_manager_id,
					email=request.POST.get('email'),
					telephone=request.POST.get('telephone'),
					active=request.POST.get('active') == '1'
				)
				
				# Create contacts
				contact_data = {}
				for key, value in request.POST.items():
					if key.startswith('contacts[') and value:
						# Parse contacts[0][full_name] format
						parts = key.split('[')
						if len(parts) >= 3:
							idx = parts[1].rstrip(']')
							field = parts[2].rstrip(']')
							if idx not in contact_data:
								contact_data[idx] = {}
							contact_data[idx][field] = value
				
				for contact in contact_data.values():
					if contact.get('full_name'):  # Only create if has name
						ContactPerson.objects.create(
							company=company,
							full_name=contact.get('full_name', ''),
							title=contact.get('title', ''),
							email=contact.get('email', ''),
							telephone=contact.get('telephone', '')
						)
				
				# Create addresses
				address_data = {}
				for key, value in request.POST.items():
					if key.startswith('addresses[') and value:
						# Parse addresses[0][name] format
						parts = key.split('[')
						if len(parts) >= 3:
							idx = parts[1].rstrip(']')
							field = parts[2].rstrip(']')
							if idx not in address_data:
								address_data[idx] = {}
							address_data[idx][field] = value
				
				for address in address_data.values():
					if address.get('name') or address.get('address'):  # Only create if has name or address
						Address.objects.create(
							company=company,
							name=address.get('name', 'Merkez'),
							country_id=address.get('country') or None,
							city_id=address.get('city') or None,
							county_id=address.get('county') or None,
							district_id=address.get('district') or None,
							zipcode=address.get('zipcode', ''),
							address=address.get('address', '')
						)
				
				# Create working hours if provided
				daily_hours = request.POST.get('daily_working_hours')
				if daily_hours:
					try:
						WorkingHours.objects.create(
							customer=company,
							daily_working_hours=int(daily_hours),
							working_on_saturday=request.POST.get('working_on_saturday') == '1',
							working_on_sunday=request.POST.get('working_on_sunday') == '1'
						)
					except (ValueError, TypeError):
						pass  # Skip if invalid data
				
				messages.success(request, _('Customer created successfully!'))
				return redirect('customer:customer_detail', pk=company.pk)
				
		except Exception as e:
			messages.error(request, f'Error creating customer: {str(e)}')
	
	# GET request - show form
	User = get_user_model()
	user = request.user
	
	managers = list(User.objects.filter(role__in=['manager_main', 'salesmanager_main'])
		.values('id', 'first_name', 'last_name', 'email'))
	# Compose full_name for dropdown
	for m in managers:
		m['id'] = str(m['id'])
		m['full_name'] = f"{m['first_name']} {m['last_name']}".strip() or m['email']
	core_businesses = list(CoreBusiness.objects.all().values('id', 'name'))
	countries = list(Country.objects.all().values('id', 'name'))
	
	# Filter companies based on user role
	if user.role in ['manager_distributor', 'salesmanager_distributor', 'service_distributor'] and user.company:
		# For distributor users, only show their own distributor company
		companies = [{'id': user.company.id, 'name': user.company.name}]
	else:
		# For main company users, show all main/distributor companies
		companies = list(Company.objects.filter(company_type__in=['main', 'distributor']).values('id', 'name'))
	
	# Pass user context for template logic
	context = {
		'managers': managers,
		'core_businesses': core_businesses,
		'countries': countries,
		'companies': companies,
		'is_distributor_user': user.role in ['manager_distributor', 'salesmanager_distributor', 'service_distributor'],
		'default_related_manager_id': user.company.related_manager.id if (user.role in ['manager_distributor', 'salesmanager_distributor', 'service_distributor'] and user.company and user.company.related_manager) else None,
	}
	
	return render(request, 'pages/customer/customer-create.html', context)

def can_user_edit_customer(user, company):
    """
    Check if user can edit the given customer company.
    """
    if not user.is_authenticated:
        return False
    
    role = getattr(user, 'role', None)
    
    # Admin, Main Company Manager, Main Company Service Personnel: can edit all
    if role in ['manager_main', 'service_main'] or user.is_superuser:
        return True
    
    # Main Company Sales Manager: can edit only companies where they are related_manager
    elif role == 'salesmanager_main':
        return company.related_manager == user
    
    # Distributor roles: can edit only companies where their company is related_company
    elif role in ['manager_distributor', 'salesmanager_distributor', 'service_distributor'] and user.company:
        return company.related_company == user.company
    
    return False


@login_required(login_url='login')
def customer_update(request, pk):
	company = get_object_or_404(Company, pk=pk)
	
	# Check if user can edit this customer
	if not can_user_edit_customer(request.user, company):
		from django.core.exceptions import PermissionDenied
		raise PermissionDenied("You don't have permission to edit this customer.")
	
	if request.method == 'POST':
		try:
			with transaction.atomic():
				# Determine related_company based on user role
				related_company_id = request.POST.get('related_company') or None
				company_type = request.POST.get('company_type')
				related_manager_id = request.POST.get('related_manager') or None
				user = request.user
				
				# If user is distributor_manager or service, auto-set their distributor as related company
				if user.role in ['manager_distributor', 'salesmanager_distributor', 'service_distributor'] and user.company:
					related_company_id = user.company.id
					company_type = 'enduser'  # Auto-set to End User
					# Set related manager to the distributor's related manager
					if user.company.related_manager:
						related_manager_id = user.company.related_manager.id
				
				# Update the company
				company.name = request.POST.get('name')
				company.company_type = company_type
				company.core_business_id = request.POST.get('core_business') or None
				company.related_company_id = related_company_id
				company.related_manager_id = related_manager_id
				company.email = request.POST.get('email')
				company.telephone = request.POST.get('telephone')
				company.active = request.POST.get('active') == '1'
				company.save()
				
				# Delete existing contacts and addresses, then recreate
				company.contactperson_set.all().delete()
				company.address.all().delete()
				
				# Create contacts
				contact_data = {}
				for key, value in request.POST.items():
					if key.startswith('contacts[') and value:
						# Parse contacts[0][full_name] format
						parts = key.split('[')
						if len(parts) >= 3:
							idx = parts[1].rstrip(']')
							field = parts[2].rstrip(']')
							if idx not in contact_data:
								contact_data[idx] = {}
							contact_data[idx][field] = value
				
				for contact in contact_data.values():
					if contact.get('full_name'):  # Only create if has name
						ContactPerson.objects.create(
							company=company,
							full_name=contact.get('full_name', ''),
							title=contact.get('title', ''),
							email=contact.get('email', ''),
							telephone=contact.get('telephone', '')
						)
				
				# Create addresses
				address_data = {}
				for key, value in request.POST.items():
					if key.startswith('addresses[') and value:
						# Parse addresses[0][name] format
						parts = key.split('[')
						if len(parts) >= 3:
							idx = parts[1].rstrip(']')
							field = parts[2].rstrip(']')
							if idx not in address_data:
								address_data[idx] = {}
							address_data[idx][field] = value
				
				for address in address_data.values():
					if address.get('name') or address.get('address'):  # Only create if has name or address
						Address.objects.create(
							company=company,
							name=address.get('name', 'Merkez'),
							country_id=address.get('country') or None,
							city_id=address.get('city') or None,
							county_id=address.get('county') or None,
							district_id=address.get('district') or None,
							zipcode=address.get('zipcode', ''),
							address=address.get('address', '')
						)
				
				# Update or create working hours
				daily_hours = request.POST.get('daily_working_hours')
				if daily_hours:
					try:
						working_hours, created = WorkingHours.objects.get_or_create(
							customer=company,
							defaults={
								'daily_working_hours': int(daily_hours),
								'working_on_saturday': request.POST.get('working_on_saturday') == '1',
								'working_on_sunday': request.POST.get('working_on_sunday') == '1'
							}
						)
						if not created:
							working_hours.daily_working_hours = int(daily_hours)
							working_hours.working_on_saturday = request.POST.get('working_on_saturday') == '1'
							working_hours.working_on_sunday = request.POST.get('working_on_sunday') == '1'
							working_hours.save()
					except (ValueError, TypeError):
						pass  # Skip if invalid data
				
				messages.success(request, _('Customer updated successfully!'))
				return redirect('customer:customer_detail', pk=company.pk)
				
		except Exception as e:
			messages.error(request, f'Error updating customer: {str(e)}')
	
	# GET request - show form with existing data
	User = get_user_model()
	user = request.user
	
	managers = list(User.objects.filter(role__in=['manager_main', 'salesmanager_main'])
		.values('id', 'first_name', 'last_name', 'email'))
	# Compose full_name for dropdown
	for m in managers:
		m['id'] = str(m['id'])
		m['full_name'] = f"{m['first_name']} {m['last_name']}".strip() or m['email']
	core_businesses = list(CoreBusiness.objects.all().values('id', 'name'))
	countries = list(Country.objects.all().values('id', 'name'))
	
	# Filter companies based on user role
	if user.role in ['manager_distributor', 'salesmanager_distributor', 'service_distributor'] and user.company:
		# For distributor users, only show their own distributor company
		companies = [{'id': user.company.id, 'name': user.company.name}]
	else:
		# For main company users, show all main/distributor companies
		companies = list(Company.objects.filter(company_type__in=['main', 'distributor']).values('id', 'name'))
	
	# Get existing contacts and addresses
	contacts = list(company.contactperson_set.all().values('full_name', 'title', 'email', 'telephone'))
	addresses = []
	for address in company.address.all():
		addr_data = {
			'name': address.name,
			'country': address.country.id if address.country else None,
			'city': address.city.id if address.city else None,
			'county': address.county.id if address.county else None,
			'district': address.district.id if address.district else None,
			'zipcode': address.zipcode,
			'address': address.address,
		}
		# Add related location data for dropdowns
		if address.country:
			addr_data['cities'] = list(City.objects.filter(country=address.country).values('id', 'name'))
		else:
			addr_data['cities'] = []
		if address.city:
			addr_data['counties'] = list(County.objects.filter(city=address.city).values('id', 'name'))
		else:
			addr_data['counties'] = []
		if address.county:
			addr_data['districts'] = list(District.objects.filter(county=address.county).values('id', 'name'))
		else:
			addr_data['districts'] = []
		addresses.append(addr_data)
	
	
	
	# Get working hours data
	try:
		working_hours = company.working_hours
		working_hours_data = {
			'daily_working_hours': working_hours.daily_working_hours,
			'working_on_saturday': working_hours.working_on_saturday,
			'working_on_sunday': working_hours.working_on_sunday
		}
	except WorkingHours.DoesNotExist:
		working_hours_data = {
			'daily_working_hours': 8,
			'working_on_saturday': False,
			'working_on_sunday': False
		}
	
	# Prepare company data for JSON
	company_data = {
		'name': company.name,
		'company_type': company.company_type,
		'core_business': company.core_business.id if company.core_business else None,
		'related_company': company.related_company.id if company.related_company else None,
		'related_manager': company.related_manager.id if company.related_manager else None,
		'email': company.email,
		'telephone': company.telephone,
		'active': company.active,
	}

	# Pass user context for template logic
	context = {
		'company': company,
		'company_data': company_data,
		'managers': managers,
		'core_businesses': core_businesses,
		'countries': countries,
		'companies': companies,
		'contacts': contacts,
		'addresses': addresses,
		'working_hours': working_hours_data,
		'is_distributor_user': user.role in ['manager_distributor', 'salesmanager_distributor', 'service_distributor'],
		'default_related_manager_id': user.company.related_manager.id if (user.role in ['manager_distributor', 'salesmanager_distributor', 'service_distributor'] and user.company and user.company.related_manager) else None,
	}
	
	return render(request, 'pages/customer/customer-update.html', context)

@login_required(login_url='login')
def api_countries(request):
	# Used for dynamic address tab (country select)
	countries = list(Country.objects.all().values('id', 'name'))
	return JsonResponse(countries, safe=False)

@login_required(login_url='login')
def api_cities(request):
	# Used for dynamic address tab (city select)
	country_id = request.GET.get('country')
	cities = City.objects.filter(country_id=country_id).values('id', 'name') if country_id else []
	return JsonResponse(list(cities), safe=False)

@login_required(login_url='login')
def api_counties(request):
	# Used for dynamic address tab (county select)
	city_id = request.GET.get('city')
	counties = County.objects.filter(city_id=city_id).values('id', 'name') if city_id else []
	return JsonResponse(list(counties), safe=False)

@login_required(login_url='login')
def api_districts(request):
	# Used for dynamic address tab (district select)
	county_id = request.GET.get('county')
	districts = District.objects.filter(county_id=county_id).values('id', 'name') if county_id else []
	return JsonResponse(list(districts), safe=False)




@login_required(login_url='login')
def api_core_businesses(request):
	core_businesses = CoreBusiness.objects.all().values('id', 'name')
	return JsonResponse(list(core_businesses), safe=False)
