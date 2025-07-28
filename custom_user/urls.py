from django.urls import path
from django.contrib.auth import views as auth_views

app_name = 'custom_user'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='custom_user:login'), name='logout'),
]
