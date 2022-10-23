from django.urls import include, path
from product.views import *


urlpatterns = [
    path('all_links/', all_links, name='all_links'),
    path('shop/', shop_main_page, name='main_page'),
    path('shop/all/', all_product_page, name='all_product_page'),
    path('shop/basket/', basket, name='basket_page'),
    path('shop/category/<int:pk>/', category_page, name='category_page'),
    path('shop/currency', select_curr, name='category_page'),
    path('shop/change_invoice/', change_invoice, name='change_invoice'),
    path('shop/courier_page/', courier_page, name='courier_page'),
    path('shop/calc_delivery/', calc_delivery, name='calc_delivery'),
    path('shop/checkout/', checkout_page, name='checkout_page'),
    path('shop/create_promocode/', create_promocode, name='create_promocode_page'),
    path('shop/edit_price_in_category/', edit_price_in_category, name='edit_price_in_category'),
    path('shop/export/', export_products, name='export_products'),
    path('shop/invoices/', all_invoices, name='invoices_page'),
    path('shop/invoice/<int:pk>/', get_invoice, name='invoice_page'),
    path('shop/invoice/<int:pk>/edit/', edit_invoice, name='invoice_edit_page'),
    path('shop/import/', import_products, name = 'import_products'),
    path('shop/matrix/', matrix, name = 'matrix'),
    path('shop/product/<int:pk>/', product_page, name='product_page'),
    path('shop/rating_product/', rating_product, name='rating_product'),
    path('shop/wishlist/', wishlist, name = 'wishlist'),
    path('shop/select_courier/', select_courier, name = 'select_courier'),
    path('shop/subeditprice/', subeditprice, name = 'subeditprice'),
    path('shop/subactivateproduct/', subactivateproduct, name = 'subactivateproduct'),
    path('shop/parser_rozetka/', parser_rozetka_view, name='parser_rozetka'),
    path('shop/update_cities_np/', update_cities_np, name = 'update_cities_np'),
    path('shop/update_warehouses_np/', update_warehouses_np, name = 'update_warehouses_np'),
]