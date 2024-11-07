from django.urls import path
from .views import (
    home, ManageCategoriesView, ProductManageView, 
    RackManageView, LayerManageView, PositionManageView
)

urlpatterns = [
    path('', home, name='home'),
    path('manage_categories/', ManageCategoriesView.as_view(), name='manage_categories'),
    
    path('products/manage/', ProductManageView.as_view(), name='manage_product'),  # Combined path for product management

    path('racks/manage/', RackManageView.as_view(), name='manage_rack'),  # Combined path for rack management

    path('layers/manage/', LayerManageView.as_view(), name='manage_layer'),  # Combined path for layer management

    path('positions/manage/', PositionManageView.as_view(), name='manage_position'),  # Combined path for position management
]
