from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import get_language
from django.conf import settings


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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Sadece yeni kullanıcı oluşturuluyorsa mail gönder
        if not change:
            language = getattr(obj, 'language', None) or get_language() or 'en'
            context = {'user': obj, 'language': language}
            subject = 'Hoş geldiniz!' if language == 'tr' else 'Welcome!'
            html_content = render_to_string('emails/user_welcome.html', context)
            from_email = settings.DEFAULT_FROM_EMAIL
            try:
                email = EmailMultiAlternatives(
                    subject,
                    html_content,
                    from_email,
                    [obj.email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
            except Exception as e:
                import logging
                logging.error(f"Mail gönderilemedi: {e}")
