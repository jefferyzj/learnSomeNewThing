from django.urls import path
from . import views

urlpatterns = [
<<<<<<< HEAD
    path('', views.product_list, name='product_list'), 
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/new/', views.add_product, name='add_product'), 
    path('product/<int:pk>/move/', views.move_product, name='move_product'),
=======
    #path('', views.home_greeting, name='home_greeting'),
    path('', views.home_page, name = 'buttom_to_product'),
    path('products/', views.product_page, name='product_page'),
>>>>>>> 5ae4491009477a99d242e8a76732abf50092fc5b
    
]
