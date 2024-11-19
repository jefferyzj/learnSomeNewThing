from django.contrib import admin
from .models import Category, Rack, Layer, Space, Location, Status, Task, StatusTask, Product, ProductTask, ResultOfStatus

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Rack)
class RackAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    list_display = ('rack', 'layer_number')
    search_fields = ('rack__name', 'layer_number')
    list_filter = ('rack',)

@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ('layer', 'space_number')
    search_fields = ('layer__rack__name', 'layer__layer_number', 'space_number')
    list_filter = ('layer',)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('rack', 'layer', 'space')
    search_fields = ('rack__name', 'layer__layer_number', 'space__space_number')

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(StatusTask)
class StatusTaskAdmin(admin.ModelAdmin):
    list_display = ('status', 'task')

@admin.register(ProductTask)
class ProductTaskAdmin(admin.ModelAdmin):
    list_display = ('product', 'task', 'is_completed', 'created_at', 'is_default', 'timestamp')

@admin.register(ResultOfStatus)
class ResultOfStatusAdmin(admin.ModelAdmin):
    list_display = ('product', 'status', 'summary_result', 'created_at')

class ProductTaskInline(admin.TabularInline):
    model = ProductTask
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('SN', 'category', 'priority_level', 'status', 'location', 'created_at')
    search_fields = ('SN', 'category__name', 'status__name')
    list_filter = ('priority_level', 'status', 'created_at')
    ordering = ('-created_at',)
    inlines = [ProductTaskInline]
    readonly_fields = ('created_at',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('action', 'can_be_skipped', 'result')
    search_fields = ('action',)
    list_filter = ('can_be_skipped',)
