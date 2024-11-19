from django.contrib import admin
from .models import Category, Location, Status, Task, StatusTask, Product, ProductTask, ResultOfStatus

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('rack_name', 'layer_number', 'space_number')
    search_fields = ('rack_name', 'layer_number', 'space_number')
    list_filter = ('rack_name', 'layer_number', 'space_number')

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('action', 'description', 'can_be_skipped', 'result', 'note')
    search_fields = ('action', 'description', 'result', 'note')
    list_filter = ('can_be_skipped',)

@admin.register(StatusTask)
class StatusTaskAdmin(admin.ModelAdmin):
    list_display = ('status', 'task')
    search_fields = ('status__name', 'task__action')
    list_filter = ('status', 'task')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('SN', 'category', 'priority_level', 'description', 'status', 'location')
    search_fields = ('SN', 'category__name', 'description', 'status__name', 'location__rack_name')
    list_filter = ('category', 'priority_level', 'status', 'location__rack_name')

@admin.register(ProductTask)
class ProductTaskAdmin(admin.ModelAdmin):
    list_display = ('product', 'task', 'is_completed', 'is_default', 'timestamp')
    search_fields = ('product__SN', 'task__action')
    list_filter = ('is_completed', 'is_default', 'timestamp')

@admin.register(ResultOfStatus)
class ResultOfStatusAdmin(admin.ModelAdmin):
    list_display = ('product', 'status', 'summary_result', 'created')
    search_fields = ('product__SN', 'status__name', 'summary_result')
    list_filter = ('status', 'created')
