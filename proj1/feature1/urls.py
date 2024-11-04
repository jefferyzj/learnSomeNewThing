from django.urls import path
from . import views

urlpatterns = [
    #path('', views.home_greeting, name='home_greeting'),
    path('', views.home_page, name = 'buttom_to_product'),
    path('products/', views.product_page, name='product_page'),
    
]
