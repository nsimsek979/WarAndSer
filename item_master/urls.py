from django.urls import path
from . import views

app_name="item-master"


urlpatterns = [
    path('', views.item_master_list, name='item_master_list'),
    path('create/', views.item_master_create, name='item_master_create'),
    path('<int:pk>/', views.item_master_detail, name='item_master_detail'),
    path('<int:pk>/edit/', views.item_master_update, name='item_master_update'),
    
    # Inventory Items
    path('inventory/', views.inventory_item_list, name='inventory_item_list'),
    path('inventory/create/', views.inventory_item_create, name='inventory_item_create'),
    path('inventory/<int:pk>/', views.inventory_item_detail, name='inventory_item_detail'),
    path('inventory/<int:pk>/edit/', views.inventory_item_update, name='inventory_item_update'),
    path('inventory/<int:pk>/delete/', views.inventory_item_delete, name='inventory_item_delete'),
    
    # AJAX views
    path('ajax/get-attribute-units/', views.get_attribute_units, name='get_attribute_units'),
    path('ajax/get-attribute-units/', views.get_attribute_units, name='get_attribute_units'),
]
