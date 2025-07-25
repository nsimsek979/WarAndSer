from django.urls import path
from . import views
app_name ="dashboard"

urlpatterns = [
    path('', views.home, name='home'),
    path('reports/core-business/', views.core_business_report, name='core_business_report'),
]
