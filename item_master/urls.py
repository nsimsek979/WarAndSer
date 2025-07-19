from django.urls import path
from . import views

app_name="item-master"


urlpatterns = [
    path('', views.item_master_list, name='item_master_list'),
    path('create/', views.item_master_create, name='item_master_create'),
    path('<int:pk>/', views.item_master_detail, name='item_master_detail'),
    path('<int:pk>/edit/', views.item_master_update, name='item_master_update'),
]
