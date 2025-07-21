from django.contrib import admin
from .models import Country, City, County, District, CoreBusiness, Company, ContactPerson, Address, WorkingHours
from django.utils.html import format_html


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


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
	list_display = ("name", "company_type", "core_business", "email", "telephone", "active", "related_manager")
	list_filter = ("company_type", "related_manager", "related_company")
	search_fields = ("name",)
	inlines = [ContactPersonInline, AddressInline, WorkingHoursInline, RelatedCompanyInline]
	autocomplete_fields = ["related_manager", "related_company"]
	fieldsets = (
		(None, {
			'fields': ("name", "company_type", "core_business", "related_manager", "email", "telephone", "active", "related_company")
		}),
	)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "display_flag")
    readonly_fields = ("display_flag",)

    def display_flag(self, obj):
        if obj.flag:
            return format_html('<img src="{}" width="50" height="30" />', obj.flag.url)
        return "-"

    display_flag.short_description = "Flag Preview"

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
	list_display = ("name", "country")

@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
	list_display = ("name", "city")

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
	list_display = ("name", "county")

@admin.register(CoreBusiness)
class CoreBusinessAdmin(admin.ModelAdmin):
	list_display = ("name",)


@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
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
