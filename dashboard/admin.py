from django.contrib import admin
from django.urls import path
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.contrib import messages
from django.contrib.admin import AdminSite
from django.apps import apps
import subprocess


# Custom Admin Site to add dashboard functionality
class GarantiVeServisAdminSite(AdminSite):
    site_header = 'Garanti ve Servis Yönetimi'
    site_title = 'GVS Admin'
    index_title = 'Yönetim Paneli'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('populate-turkish-locations/', self.admin_view(self.populate_locations_view), name='populate-turkish-locations'),
        ]
        return custom_urls + urls
    
    def populate_locations_view(self, request):
        if request.method == 'POST':
            try:
                result = subprocess.run([
                    'python', 'manage.py', 'populate_turkish_locations'
                ], capture_output=True, text=True, cwd=r'd:\GarantiVeServis')
                if result.returncode == 0:
                    messages.success(request, 'Lokasyonlar başarıyla güncellendi!')
                else:
                    messages.error(request, result.stderr or 'Komut çalıştırılamadı.')
            except Exception as e:
                messages.error(request, f'Hata oluştu: {str(e)}')
            return HttpResponseRedirect(request.path)
        
        context = dict(
            self.each_context(request),
            title='Türkiye Lokasyonlarını Güncelle',
        )
        return TemplateResponse(request, 'dashboard/admin_populate_locations.html', context)
    
    def index(self, request, extra_context=None):
        """Override admin index to add custom actions"""
        extra_context = extra_context or {}
        
        # Add custom dashboard actions
        extra_context.update({
            'dashboard_actions': [
                {
                    'title': 'Türkiye Lokasyonlarını Güncelle',
                    'description': 'İl ve ilçe verilerini güncelleyin',
                    'url': 'admin:populate-turkish-locations',
                    'icon': '🏛️'
                }
            ]
        })
        
        return super().index(request, extra_context)


# Create custom admin site instance
garanti_ve_servis_admin_site = GarantiVeServisAdminSite(name='gvs_admin')

# Auto-register all models from all apps
for app_config in apps.get_app_configs():
    for model in app_config.get_models():
        try:
            # Skip already registered models
            if not garanti_ve_servis_admin_site.is_registered(model):
                garanti_ve_servis_admin_site.register(model)
        except Exception:
            # Skip models that can't be registered
            pass