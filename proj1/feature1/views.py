from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Position
from .forms import ProductForm, MoveProductForm

def home(request):
    return render(request, 'home.html')

def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})


def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm()
    return render(request, 'product_form.html', {'form': form})

def move_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = MoveProductForm(request.POST, instance=product)
        if form.is_valid():
            product.position = form.cleaned_data['new_position']
            product.save()
            return redirect('product_detail', pk=product.pk)
    else:
        form = MoveProductForm(instance=product)
    return render(request, 'move_product_form.html', {'form': form, 'product': product})
