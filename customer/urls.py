from django.urls import path
from . import views

app_name = "customer"

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('create/', views.customer_create, name='customer_create'),
    path('<int:pk>/update/', views.customer_update, name='customer_update'),
    path('api/countries/', views.api_countries, name='api_countries'),
    path('api/managers/', views.api_managers, name='api_managers'),
    path('api/core-businesses/', views.api_core_businesses, name='api_core_businesses'),
    path('api/cities/', views.api_cities, name='api_cities'),
    path('api/counties/', views.api_counties, name='api_counties'),
    path('api/districts/', views.api_districts, name='api_districts'),
    path('<int:pk>/', views.customer_detail, name='customer_detail'),
]
