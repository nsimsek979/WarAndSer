from django.contrib import admin
from .models import Country, City, County, District, CoreBusiness, Company, ContactPerson, Address
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

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
	list_display = ("name", "company_type", "core_business", "email", "telephone", "active", "related_manager")
	list_filter = ("company_type", "related_manager", "related_company")
	search_fields = ("name",)
	inlines = [ContactPersonInline, AddressInline, RelatedCompanyInline]
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
