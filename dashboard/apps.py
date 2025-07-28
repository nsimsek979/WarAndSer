from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"
    
    def ready(self):
        from django.contrib import admin
        admin.site.site_header = 'Garanti ve Servis Yönetimi'
        admin.site.site_title = 'GVS Admin'
        admin.site.index_title = 'Yönetim Paneli'
