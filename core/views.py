
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib import messages


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        """Role-based redirection after login"""
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'role'):
            # Service personnel rolleri için warranty-services'e yönlendir
            if user.role in ['service_main', 'service_distributor']:
                return reverse_lazy('warranty_and_services:mobile_main')
        
        # Diğer roller için default dashboard
        return reverse_lazy('dashboard:home')


# Create your views here.
@login_required(login_url='login')
def profile(request):
	return render(request, 'pages/profile.html')
