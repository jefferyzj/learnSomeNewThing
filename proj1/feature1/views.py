from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Product, Category, Rack, Layer, Position
from .forms import ProductForm, MoveProductForm, CategoryForm, RackForm, LayerForm, PositionForm

def home(request):
    return render(request, 'home.html')

class ManageCategoriesView(View):
    template_name = 'manage_categories.html'

    def get(self, request):
        categories = Category.objects.all()
        form = CategoryForm()
        return render(request, self.template_name, {'categories': categories, 'form': form})

    def post(self, request):
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_categories')
        categories = Category.objects.all()
        return render(request, self.template_name, {'categories': categories, 'form': form})

class ProductManageView(View):
    template_name = 'product_form.html'

    def get(self, request, pk=None):
        if pk:
            product = get_object_or_404(Product, pk=pk)
            form = ProductForm(instance=product)
            context = {'form': form, 'product': product}
        else:
            form = ProductForm()
            context = {'form': form}
        return render(request, self.template_name, context)

    def post(self, request, pk=None):
        if pk:
            product = get_object_or_404(Product, pk=pk)
            form = ProductForm(request.POST, instance=product)
            if form.is_valid():
                product = form.save(commit=False)
                product.position = form.cleaned_data.get('new_position') or product.position
                product.save()
                return redirect('manage_product')
            context = {'form': form, 'product': product}
        else:
            form = ProductForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('manage_product')
            context = {'form': form}
        return render(request, self.template_name, context)

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        return redirect('manage_product')

