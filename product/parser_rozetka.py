import requests
from product.models import Product, Categories
import re
from time import sleep



def get_all_ids_goods(id_cat):
    req = requests.get(f'https://xl-catalog-api.rozetka.com.ua/v3/goods/get?front-type=xl&category_id={id_cat}')
    if req.status_code == 200:
        all_request = req.json()
        ids_goods = all_request['data']['ids']
        get_goods_info(ids_goods, id_cat)
        total_pages_category = all_request['data']['total_pages']
        for id_page in range(2, total_pages_category+1):
            sleep(1)
            req_for_get_id_goods = requests.get(f'https://xl-catalog-api.rozetka.com.ua/v3/goods/get?front-type=xl&category_id={id_cat}&page={id_page}')
            if req_for_get_id_goods.status_code == 200:
                temp_ids_goods = req_for_get_id_goods.json()
                get_goods_info(temp_ids_goods, id_cat)
                ids_goods += temp_ids_goods['data']['ids']

    else:
        return('Категория не найдена. Попробуй ввести другой ID', req.url)
            

        
def get_goods_info(lst_ids, id_category):
    req_goods = requests.get(f'https://xl-catalog-api.rozetka.com.ua/v3/goods/getDetails?product_ids={lst_ids}')
    if req_goods.status_code == 200:
        all_goods = req_goods.json()
        all_goods = all_goods['data']
        good_info = {}
        for good in all_goods:
            #собираем нужную инфу про товар
            title_product = good.get('title')
            link = f'https://xl-catalog-api.rozetka.com.ua/v4/categories/get?front-type=xl&country=UA&lang=ru&id={good.get("category_id")}'
            req = requests.get(link).json()
            cat_name = req['data']['category']['title']
            category, cr = Categories.objects.get_or_create(
                name = cat_name
            )
            good_info['brand'] = good.get('brand')
            good_info['desc'] = good.get('docket').replace('\n', '').replace('\r', '')
            good_info['price'] = good.get('price')
            good_info['old_price'] = good.get('old_price')
            product_obj, product_new = Product.objects.update_or_create(
                title = title_product,
                defaults = good_info
            )
            if product_new:
                product_obj.cid.add(category)
            else:
                product_obj.cid.set([category])