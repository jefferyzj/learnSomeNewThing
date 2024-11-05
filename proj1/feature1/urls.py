from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'), 
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/new/', views.add_product, name='add_product'), 
    path('product/<int:pk>/move/', views.move_product, name='move_product'),
    
]
