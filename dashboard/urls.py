from django.urls import path
from . import views
app_name ="dashboard"

urlpatterns = [
    path('', views.home, name='home'),
    path('reports/core-business/', views.core_business_report, name='core_business_report'),
    path('reports/distributor/', views.distributor_report, name='distributor_report'),
    path('reports/category/', views.category_report, name='category_report'),
    path('reports/breakdown-maintenance/', views.breakdown_maintenance_report, name='breakdown_maintenance_report'),
    path('reports/spare-parts/', views.spare_parts_report, name='spare_parts_report'),
]
