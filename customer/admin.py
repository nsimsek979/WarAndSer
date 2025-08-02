from django.contrib import admin
from django.utils.html import format_html
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, DateTimeWidget
from django.utils import timezone
from .models import Country, City, County, District, CoreBusiness, Company, ContactPerson, Address, WorkingHours

class NaiveDateTimeWidget(DateTimeWidget):
    """Custom widget to remove timezone info from datetime objects for Excel export"""
    def render(self, value, obj=None, **kwargs):
        if value and hasattr(value, 'replace'):
            # Remove timezone info
            value = value.replace(tzinfo=None)
        return super().render(value, obj, **kwargs)


class ContactPersonInline(admin.TabularInline):
	model = ContactPerson
	extra = 1

class AddressInline(admin.TabularInline):
	model = Address
	extra = 1

class RelatedCompanyInline(admin.TabularInline):
	model = Company
	fk_name = 'related_company'
	extra = 1


class WorkingHoursInline(admin.StackedInline):
	model = WorkingHours
	extra = 0
	readonly_fields = ('weekly_working_hours_display', 'working_days_display')
	
	def weekly_working_hours_display(self, obj):
		if obj.pk:
			return f"{obj.weekly_working_hours} hours/week"
		return "-"
	weekly_working_hours_display.short_description = "Weekly Working Hours"
	
	def working_days_display(self, obj):
		if obj.pk:
			return f"{obj.get_working_days_per_week()} days/week"
		return "-"
	working_days_display.short_description = "Working Days"


# Import/Export Resources
class CountryResource(resources.ModelResource):
    class Meta:
        model = Country
        fields = ('name', 'code')
        exclude = ('id',)
        import_id_fields = ['name']


class CityResource(resources.ModelResource):
    country = fields.Field(
        column_name='country',
        attribute='country',
        widget=ForeignKeyWidget(Country, 'name')
    )
    
    class Meta:
        model = City
        fields = ('name', 'country')
        exclude = ('id',)
        import_id_fields = ['name']


class CountyResource(resources.ModelResource):
    city = fields.Field(
        column_name='city',
        attribute='city',
        widget=ForeignKeyWidget(City, 'name')
    )
    
    class Meta:
        model = County
        fields = ('name', 'city')
        exclude = ('id',)
        import_id_fields = ['name']


class DistrictResource(resources.ModelResource):
    county = fields.Field(
        column_name='county',
        attribute='county',
        widget=ForeignKeyWidget(County, 'name')
    )
    
    class Meta:
        model = District
        fields = ('name', 'county')
        exclude = ('id',)
        import_id_fields = ['name']


class CoreBusinessResource(resources.ModelResource):
    class Meta:
        model = CoreBusiness
        fields = ('name',)
        exclude = ('id',)
        import_id_fields = ['name']


class CompanyResource(resources.ModelResource):
    core_business = fields.Field(
        column_name='core_business',
        attribute='core_business',
        widget=ForeignKeyWidget(CoreBusiness, 'name')
    )
    related_company = fields.Field(
        column_name='related_company',
        attribute='related_company',
        widget=ForeignKeyWidget(Company, 'name')
    )
    related_manager = fields.Field(
        column_name='related_manager',
        attribute='related_manager',
        widget=ForeignKeyWidget('custom_user.CustomUser', 'username')
    )
    
    class Meta:
        model = Company
        fields = ('name', 'company_type', 'core_business', 'related_manager', 'email', 'telephone', 'active', 'related_company')
        exclude = ('id',)
        import_id_fields = ['name']


class ContactPersonResource(resources.ModelResource):
    company = fields.Field(
        column_name='company',
        attribute='company',
        widget=ForeignKeyWidget(Company, 'name')
    )
    
    class Meta:
        model = ContactPerson
        fields = ('company', 'full_name', 'title', 'email', 'telephone')
        exclude = ('id',)
        import_id_fields = ['company', 'full_name']


class AddressResource(resources.ModelResource):
    company = fields.Field(
        column_name='company',
        attribute='company',
        widget=ForeignKeyWidget(Company, 'name')
    )
    country = fields.Field(
        column_name='country',
        attribute='country',
        widget=ForeignKeyWidget(Country, 'name')
    )
    city = fields.Field(
        column_name='city',
        attribute='city',
        widget=ForeignKeyWidget(City, 'name')
    )
    county = fields.Field(
        column_name='county',
        attribute='county',
        widget=ForeignKeyWidget(County, 'name')
    )
    district = fields.Field(
        column_name='district',
        attribute='district',
        widget=ForeignKeyWidget(District, 'name')
    )
    
    class Meta:
        model = Address
        fields = ('company', 'name', 'country', 'city', 'county', 'district', 'zip_code', 'address')
        exclude = ('id',)
        import_id_fields = ['company', 'name']


class WorkingHoursResource(resources.ModelResource):
    customer = fields.Field(
        column_name='customer',
        attribute='customer',
        widget=ForeignKeyWidget(Company, 'name')
    )
    
    class Meta:
        model = WorkingHours
        fields = ('customer', 'daily_working_hours', 'working_on_saturday', 'working_on_sunday')
        exclude = ('id',)
        import_id_fields = ['customer']


@admin.register(Company)
class CompanyAdmin(ImportExportModelAdmin):
	resource_class = CompanyResource
	list_display = ("name", "company_type", "core_business", "email", "telephone", "active", "related_manager")
	list_filter = ("company_type", "active", "core_business", "related_manager", "related_company")
	search_fields = ("name", "email", "telephone")
	inlines = [ContactPersonInline, AddressInline, WorkingHoursInline, RelatedCompanyInline]
	autocomplete_fields = ["related_manager", "related_company", "core_business"]
	fieldsets = (
		(None, {
			'fields': ("name", "company_type", "core_business", "related_manager", "email", "telephone", "active", "related_company")
		}),
		('Advanced', {
			'fields': ("tax_number",),
			'classes': ('collapse',)
		}),
	)

	def get_queryset(self, request):
		"""Optimize queries with select_related"""
		qs = super().get_queryset(request)
		return qs.select_related('core_business', 'related_manager', 'related_company')

	def get_list_filter(self, request):
		"""Add dynamic filters based on company types"""
		filters = list(super().get_list_filter(request))
		
		# Add custom company type filter
		class CompanyTypeFilter(admin.SimpleListFilter):
			title = 'Company Type'
			parameter_name = 'company_type'

			def lookups(self, request, model_admin):
				return Company.COMPANY_TYPE_CHOICES

			def queryset(self, request, queryset):
				if self.value():
					return queryset.filter(company_type=self.value())
				return queryset

		filters.insert(0, CompanyTypeFilter)
		return filters

	class Media:
		js = ('admin/js/company_related_manager.js',)

	def get_form(self, request, obj=None, **kwargs):
		form = super().get_form(request, obj, **kwargs)
		
		# If it's an end user company with related_company but no related_manager,
		# try to auto-assign from related_company
		if obj and obj.company_type == 'enduser' and obj.related_company and not obj.related_manager:
			if obj.related_company.related_manager:
				obj.related_manager = obj.related_company.related_manager
				obj.save()
		
		return form

@admin.register(Country)
class CountryAdmin(ImportExportModelAdmin):
    resource_class = CountryResource
    list_display = ("name", "code", "display_flag")
    readonly_fields = ("display_flag",)
    search_fields = ['name', 'code']

    def display_flag(self, obj):
        if obj.flag:
            return format_html('<img src="{}" width="50" height="30" />', obj.flag.url)
        return "-"

    display_flag.short_description = "Flag Preview"

@admin.register(City)
class CityAdmin(ImportExportModelAdmin):
	resource_class = CityResource
	list_display = ("name", "country")
	search_fields = ['name']

@admin.register(County)
class CountyAdmin(ImportExportModelAdmin):
	resource_class = CountyResource
	list_display = ("name", "city")
	search_fields = ['name']

@admin.register(District)
class DistrictAdmin(ImportExportModelAdmin):
	resource_class = DistrictResource
	list_display = ("name", "county")
	search_fields = ['name']

@admin.register(CoreBusiness)
class CoreBusinessAdmin(ImportExportModelAdmin):
	resource_class = CoreBusinessResource
	list_display = ("name",)
	search_fields = ['name']


@admin.register(WorkingHours)
class WorkingHoursAdmin(ImportExportModelAdmin):
	resource_class = WorkingHoursResource
	list_display = (
		'customer', 
		'daily_working_hours', 
		'working_on_saturday', 
		'working_on_sunday', 
		'get_weekly_hours',
		'get_working_days',
		'updated_at'
	)
	list_filter = ('working_on_saturday', 'working_on_sunday', 'daily_working_hours')
	search_fields = ('customer__name',)
	readonly_fields = ('get_weekly_hours', 'get_working_days', 'created_at', 'updated_at')
	autocomplete_fields = ['customer']
	
	fieldsets = (
		(None, {
			'fields': ('customer', 'daily_working_hours')
		}),
		('Weekend Work', {
			'fields': ('working_on_saturday', 'working_on_sunday')
		}),
		('Calculated Values', {
			'fields': ('get_weekly_hours', 'get_working_days'),
			'classes': ('collapse',)
		}),
		('Timestamps', {
			'fields': ('created_at', 'updated_at'),
			'classes': ('collapse',)
		}),
	)
	
	def get_weekly_hours(self, obj):
		return f"{obj.weekly_working_hours} hours/week"
	get_weekly_hours.short_description = "Weekly Working Hours"
	
	def get_working_days(self, obj):
		return f"{obj.get_working_days_per_week()} days/week"
	get_working_days.short_description = "Working Days Per Week"


# Register additional models with import/export
@admin.register(ContactPerson)
class ContactPersonAdmin(ImportExportModelAdmin):
	resource_class = ContactPersonResource
	list_display = ('full_name', 'title', 'company', 'email', 'telephone')
	list_filter = ('company',)
	search_fields = ('full_name', 'title', 'email', 'company__name')
	autocomplete_fields = ['company']


@admin.register(Address)
class AddressAdmin(ImportExportModelAdmin):
	resource_class = AddressResource
	list_display = ('name', 'company', 'city', 'county', 'district')
	list_filter = ('country', 'city', 'county')
	search_fields = ('name', 'company__name', 'address')
	autocomplete_fields = ['company', 'country', 'city', 'county', 'district']
