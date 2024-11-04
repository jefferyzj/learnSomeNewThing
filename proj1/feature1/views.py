from django.shortcuts import render
from .models import Product
from django.http import HttpResponse

def home_page(request):
    #products = Product.objects.all()
    return render(request, 'home.html')

def product_page(request):
    return render(request, "product_list.html")

