from django.contrib import admin
from .models import Category, Rack, Layer, Position, Product

admin.site.register(Category)
admin.site.register(Rack)
admin.site.register(Layer)
admin.site.register(Position)
admin.site.register(Product)
