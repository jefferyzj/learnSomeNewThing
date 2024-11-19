from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Product, ProductTask, Category, StatusResult, Task

class ProductView(View):
    def get(self, request, sn=None):
        if sn:
            # If `sn` is provided, show product details
            product = get_object_or_404(Product, SN=sn)
            categories = Category.objects.all()
            if 'edit' in request.path:
                status_results = StatusResult.objects.filter(product=product).prefetch_related('tasks').order_by('-created_at')
                return render(request, 'product_edit.html', {'product': product, 'categories': categories, 'status_results': status_results})
            return render(request, 'product_detail.html', {'product': product})
        else:
            # If `sn` is not provided, list all products
            products = Product.objects.all()
            return render(request, 'products.html', {'products': products})

    def post(self, request, sn):
        product = get_object_or_404(Product, SN=sn)
        product.category = get_object_or_404(Category, id=request.POST['category'])
        product.description = request.POST['description']
        product.priority_level = request.POST['priority_level']
        product.location = request.POST['location']
        product.save()
        return redirect('product_detail', sn=product.SN)

class ProductTaskView(View):
    def get(self, request, sn):
        product = get_object_or_404(Product, SN=sn)
        ongoing_task = ProductTask.objects.filter(product=product, is_completed=False).first()
        return render(request, 'product_task.html', {'product': product, 'ongoing_task': ongoing_task})

    def post(self, request, task_id):
        task = get_object_or_404(ProductTask, id=task_id)
        if 'skip_task' in request.path:
            task.result = "This task is skipped"
            task.is_completed = True
        else:
            task.result = request.POST['result']
            task.note = request.POST['note']
            task.is_completed = 'is_completed' in request.POST
        task.save()
        return redirect('product_task', sn=task.product.SN)

class AddTaskView(View):
    def post(self, request, sn):
        product = get_object_or_404(Product, SN=sn)
        new_task = ProductTask(product=product, action="New Task", action_description="Describe the task", is_completed=False)
        new_task.save()
        return redirect('product_edit', sn=product.SN)
