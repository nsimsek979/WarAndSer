"""
URL configuration for gvs project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf.urls.i18n import set_language
from dashboard.admin import garanti_ve_servis_admin_site

urlpatterns = [
    path("admin/", garanti_ve_servis_admin_site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("core/", include("core.urls")),
    path("", include("dashboard.urls")),
    path('set_language/', set_language, name='set_language'),
    path('item-master/', include('item_master.urls')),
    path('customer/', include('customer.urls')),
    path('warranty-services/', include('warranty_and_services.urls')),
    # API endpoints for mobile app
    path('api/', include('api.urls')),
]

# Serve static and media files from development server if DEBUG is True
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
