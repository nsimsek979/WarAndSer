from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _


class RoleBasedAccessMiddleware:
    """
    Middleware to control access based on user roles
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for non-authenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)
            
        # Admin and static URLs are always allowed for everyone
        admin_static_urls = [
            '/admin/',
            '/static/',
            '/media/',
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/password_reset/',
            '/set_language/',
        ]
        
        if any(request.path.startswith(url) for url in admin_static_urls):
            return self.get_response(request)
            
        # ONLY restrict service personnel - other roles have full access
        if hasattr(request.user, 'role') and request.user.role in ['service_main', 'service_distributor']:
            # URLs that service personnel can access
            service_allowed_urls = [
                '/warranty-services/',
                '/api/',  # For mobile app
            ]
            
            # Check if service personnel is trying to access restricted area
            if not any(request.path.startswith(url) for url in service_allowed_urls):
                messages.warning(request, _('You only have access to Installation & Maintenance section.'))
                return redirect('warranty_and_services:mobile_main')
        
        # All other roles (admin, manager, etc.) have unrestricted access
        return self.get_response(request)
