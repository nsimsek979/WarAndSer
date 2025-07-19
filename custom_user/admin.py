from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('company', 'role')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('company', 'role')}),
    )
    list_display = UserAdmin.list_display + ('company', 'role', 'get_managed_companies')

    def get_managed_companies(self, obj):
        return ", ".join([c.name for c in obj.managed_companies.all()])
    get_managed_companies.short_description = "Managed Companies"
