from product.models import *
from accounts.models import *
import re
import json
from importlib import import_module
from django.conf import settings
import csv, xlsxwriter
import requests
import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.errors import HttpError
import datetime
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv
load_dotenv()
import os

from shop.storage_backends import MediaStorage
from django.core.files.base import ContentFile




class Basket:

    def get_basket(user_id = None):
        basket = {}
        if user_id:
            user = get_object_or_404(CustomUser, id = user_id)
            basket_obj = BasketItem.objects.filter(user_id = user)
            full_sum = 0 
            for i in basket_obj:
                basket[str(i.product.id)] = {
                    'id': i.product.id,
                    'title': i.product.title,
                    'type_product':i.product.type_product,
                    'qty': i.qty,
                    'price': i.price,
                }
                full_sum += i.qty * i.price
        return basket
    
    def add2basket(basket, product_id, qty, user_id = None, _type = 'add'):
        product = get_object_or_404(Product, id = product_id)
        product_info = model_to_dict(product)
        del(product_info['cid'])
        del(product_info['photo'])
        del(product_info['file_digit'])
        if not basket.get(str(product_id)):
            basket[str(product_id)] = product_info
        now_qty = basket[str(product_id)].get('qty', 0)
        end_qty = 1
        if _type == 'add':
            end_qty = now_qty + int(qty)
        elif _type == 'edit':
            end_qty = int(qty)
        basket[str(product_id)]['qty'] = end_qty
        if user_id:
            bsk, create_basket = BasketItem.objects.get_or_create(
                user = CustomUser.objects.get(id = user_id),
                product = product,
                defaults = {'qty' : end_qty,
                    'price' : product.price,})
            if not create_basket:
                bsk.qty = end_qty
                bsk.save()
        return basket


    def del2basket(basket, product_id, user_id = None):
        del(basket[str(product_id)])
        if user_id:
            product = Product.objects.get(id = product_id)
            BasketItem.objects.filter(user = CustomUser.objects.get(id = user_id), product=product).delete()
        return basket

class OrderServise:
    def filter_order(data):
        filter_order = {}
        date_default = {}
        if data.get('min_amount'):
            filter_order['total_amount__gte'] = data.get('min_amount') 
        if data.get('max_amount'):
            filter_order['total_amount__lte'] = data.get('max_amount') 
        if data.get('date_start'):
            date_default['date_start'] = data.get('date_start')
            date_start = data.get('date_start').split('-')
            date_start = list(map(int, date_start))
            filter_order['date_create__gte'] = datetime.date(*date_start)
            filter_order['date_start'] = data.get('date_start')
        if data.get('date_end'):
            date_default['date_end'] = data.get('date_end')
            date_end = data.get('date_end').split('-')
            date_end = list(map(int, date_end))
            filter_order['date_create__lte'] = datetime.date(*date_end)
            filter_order['date_end'] = data.get('date_end')
        if data.get('status'):
            filter_order['status'] = data.get('status')
        
        return filter_order


class ProductServices:

    def filter_product(data):
        filter_product = {}
        if data.get('pid'):
            try:
                filter_product['id'] = int(data.get('pid'))
            except ValueError:
                context['error'] = 'INCORRECT PARAMETRE'
        if data.get('min_price'):
            filter_product['price__gte'] = data.get('min_price') 
        if data.get('max_price'):
            filter_product['price__lte'] = data.get('max_price')         
        return filter_product

    def export_to_file(type_file):
        if type_file == 'csv':
            with open('export.csv', 'w', newline='',encoding='utf-8') as f:
                export_file = csv.DictWriter(f, fieldnames = [
                    'Название',
                    'Остаток',
                    'Бренд',
                    'Описание',
                    'Артикул',
                    'Цена',
                    'Старая цена',
                    'Категория',
                ], delimiter = '|')

                export_file.writeheader()

                all_products = Product.objects.all()
                for item in all_products:
                    all_categories = item.cid.all()
                    lst_categories = []
                    for i in all_categories:
                        lst_categories.append(i.name)
                    export_file.writerow({
                        'Название':item.title,
                        'Остаток':item.stock,
                        'Бренд':item.brand,
                        'Описание':item.desc,
                        'Артикул':item.vendor_code,
                        'Цена':item.price,
                        'Старая цена':item.old_price,
                        'Категория':';'.join(lst_categories),
                    })

            csv_file = MediaStorage().save(name = 'export.csv', content = ContentFile(open('export.csv', 'rb').read()))
            if csv_file:
                return MediaStorage().url(csv_file)
            else:
                return None
        elif type_file == 'xlsx':
            workbook = xlsxwriter.Workbook('price.xlsx')
            worksheet = workbook.add_worksheet()
            # Some data we want to write to the worksheet.
            data_for_export = (
                ['Название',
                'Остаток',
                'Бренд',
                'Описание',
                'Артикул',
                'Цена',
                'Старая цена',
                'Категория'],
            )

            row = 0
            col = 0

            all_products = Product.objects.all()
            for item in all_products:
                all_categories = item.cid.all()
                lst_categories = []
                for i in all_categories:
                    lst_categories.append(i.name)
                data_for_export = data_for_export + ([
                    item.title,
                    item.stock,
                    item.brand,
                    item.desc,
                    item.vendor_code,
                    item.price,
                    item.old_price,
                    ';'.join(lst_categories),
                ],)

            for nm, st, br, ds, vn, pr, oldpr, cat in (data_for_export):
                worksheet.write(row, col,     nm)
                worksheet.write(row, col + 1, st)
                worksheet.write(row, col + 2, br)
                worksheet.write(row, col + 3, ds)
                worksheet.write(row, col + 4, vn)
                worksheet.write(row, col + 5, pr)
                worksheet.write(row, col + 6, oldpr)
                worksheet.write(row, col + 7, cat)
                row += 1
            workbook.close()
            xlsx_file = MediaStorage().save(name = 'price.xlsx', content = ContentFile(open('export.csv', 'rb').read()))
            if xlsx_file:
                return MediaStorage().url(xlsx_file)
            else:
                return None


    def data_preparation_edit_price(lst_data) -> dict :
        """ Подготовка данных для массовой замены цен в категориях
            type_edit - тип изменения (фиксированный/проценты)
            value_edit - на сколько изменять цену
            is_edit_old_price - устанавливать ли "Цена" в "Старая цена"
            lst_cats_id - список IDs категорий
         """
        context_data = {}
        context_data['type_edit'] = lst_data.get('type_edit', 'fix')
        context_data['is_edit_old_price'] = lst_data.get('is_edit_old_price', False)
        context_data['value_edit'] = 0
        try:
            context_data['value_edit'] = float(lst_data.get('value_edit_price', 0))
        except ValueError:
            context_data['value_edit'] = 0
        mask_cats_edit = 'id_cat_'
        r = re.compile(f'{mask_cats_edit}.*')
        lts_cats = list(filter(r.match, lst_data))
        context_data['lst_cats_id'] = []
        for category in lts_cats:
            try:
                id_category = int(category[len(mask_cats_edit):])
                context_data['lst_cats_id'].append(id_category)
            except ValueError:
                pass
        return context_data
        


    def get_all_products_in_categories(lts_categories: list):
        """ lst_categories - список с ID категорий. 
        возвращает QuerySet со всеми товарами категорий  """
        return Product.objects.filter(cid__pk__in = lts_categories)


    def edit_price_products(lst_cats, type_edit: str, value_edit: float, is_edit_old_price = False):
        products = ProductServices.get_all_products_in_categories(lst_cats)
        for product in products:
            new_price = product.price
            if type_edit == 'fix':
                new_price = product.price + value_edit
            elif type_edit == 'relative':
                new_price = product.price + product.price * value_edit/100
            new_price = new_price if new_price>= 0 else 0

            if is_edit_old_price:
                product.old_price = product.price
            
            product.price = new_price
            product.save()


class ImportSheet:

    def is_correct_link(link):
        CREDENTIALS_FILE = 'creds.json'
        spreadsheet_id = ''
        re_sheet_id = re.search(r'spreadsheets/d/(.*)/', link)
        if re_sheet_id:
            spreadsheet_id = re_sheet_id.group(1)
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_FILE, 
            ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        httpAuth = credentials.authorize(httplib2.Http())
        service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)
        try:
            values = service.spreadsheets().values().get(
                spreadsheetId = spreadsheet_id,
                range = 'A1:Z20',
                majorDimension = 'ROWS'
            ).execute()
            return True
        except HttpError:
            return False

    def import_from_gsheets(link, preview = False):
        CREDENTIALS_FILE = 'creds.json'
        spreadsheet_id = ''
        cnt_rows = 10 if preview else 9999
        re_sheet_id = re.search(r'spreadsheets/d/(.*)/', link)
        if re_sheet_id:
            spreadsheet_id = re_sheet_id.group(1)

        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_FILE, 
            ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

        httpAuth = credentials.authorize(httplib2.Http())
        service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)

        values = service.spreadsheets().values().get(
            spreadsheetId = spreadsheet_id,
            range = f'A1:Z{cnt_rows}',
            majorDimension = 'ROWS'
        ).execute()

        gsheets_values = values.get('values')
        gsheets_values = ImportSheet.preparation_for_import_gsheets(gsheets_values)
        if preview:
            return gsheets_values
        for row in gsheets_values:
            if row[0] and row[1]:
                price = float(row[5])
                old_price = float(row[6])
                stock = int(row[7])
                category_exists = Categories.objects.filter(name=row[0]).exists()
                category = Categories.objects.get(name = row[0]) if category_exists else Categories(name = row[0]).save()
                default_data = {
                    'brand':row[2],
                    'desc' : row[3],
                    'vendor_code' : row[4],
                    'price' : price,
                    'old_price' : old_price,
                    'stock' : stock,
                }
                product_obj, product_new = Product.objects.get_or_create(title = row[1], defaults = default_data)
                if product_new:
                    product_obj.cid.add(category)
                else:
                    product_obj.cid.set([category])

                product_obj.brand = row[2]
                product_obj.desc = row[3]
                product_obj.vendor_code = row[4]
                product_obj.price = price
                product_obj.old_price = old_price
                product_obj.stock = stock
                product_obj.save()


    def preparation_for_import_gsheets(data_lst):
        """ дополнить все элементы пустыми значениями, чтобы все списки были равны по длине"""
        count_column = 8
        for i in data_lst:
            while len(i) < count_column:
                i.append('')

        return data_lst

    def generate_preview_to_front(lst):
        html_result = """
            <table class="table">
                <thead class="thead-light">
            <tr>
                <th scope="col">Категория</th>
                <th scope="col">Название</th>
                <th scope="col">Бренд</th>
                <th scope="col">Описание</th>
                <th scope="col">Артикул</th>
                <th scope="col">Цена</th>
                <th scope="col">Старая цена</th>
                <th scope="col">Остаток</th>
            </tr>
            </thead>
            <tbody>"""
        for row in lst:
            html_result += f'<tr>'
            html_result += f'<td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td>'
            html_result += f'<td>{row[3]}</td><td>{row[4]}</td><td>{row[5]}</td>'
            html_result += f'<td>{row[6]}</td><td>{row[7]}</td></tr>'
        html_result += '</tbody></table>'

        return html_result


class DeliveryFunc:

    def calc_cost_of_delivery(id_delivery, total_amount):
        try:
            delivery = Delivery.objects.get(pk=id_delivery)
        except Delivery.DoesNotExist:
            return {}

        if delivery.type_delivery == 'normal':
            cost = delivery.calculate_cost_of_delivery(total_amount)
            return {'cost':cost}
        elif delivery.type_delivery == 'np':
            return DeliveryFunc.novaposhta()

    
    def novaposhta(type_find = False, present_val = False, total_amount = False, warehouses = None):
        if not type_find:
            all_regions = list(DeliveryCitiesNP.objects.all().values_list('region', flat=True).distinct())
            return {'select':sorted(all_regions), 'type':'region_novaposhta'}
        elif type_find == 'region':
            all_cities = DeliveryCitiesNP.objects.values_list('city', flat=True).filter(region = present_val)
            return {'select':sorted(all_cities), 'type':'city_novaposhta'}
        elif type_find == 'city':
            try:
                city = DeliveryCitiesNP.objects.get(city=present_val)
                all_warehouses =city.deliverywarehousesnp_set.values_list('description_ru', flat=True)
                return {'select':all_warehouses, 'type':'warehouses_novaposhta', 'ref':city.city_ref}
            except DeliveryWarehousesNP.DoesNotExist:
                return {}
        elif type_find == 'warehouses':
            try:
                city = DeliveryCitiesNP.objects.get(city_ref=present_val)
                cost = city.calc_cost_of_delivery(total_amount)
                print(warehouses)
                war_val = city.deliverywarehousesnp_set.values('ref_warehouse').filter(description_ru = warehouses)
                if war_val:
                    is_warehouses = war_val[0]['ref_warehouse']
                else:
                    is_warehouses = False
                return {'cost':cost, 'war_ref':is_warehouses}
            except DeliveryCitiesNP.DoesNotExist:
                return {}


        

def update_w():
    link = 'https://api.novaposhta.ua/v2.0/json/'
    data = (
        '{"modelName": "AddressGeneral",'
        '"calledMethod": "getWarehouses",'
        '"methodProperties": {"Language": "ru"},'
        f'"apiKey": "{os.environ.get("TOKEN_NP")}"}}'
    )
    headers = {'Content-Type':'application/json',}
    req = requests.post(link, data=data, headers=headers)
    responce = req.json()
    cnt = 0
    if responce.get('success'):
        for item in responce['data']:
            cnt+=1
            print(cnt)
            try:
                city = DeliveryCitiesNP.objects.get(city_ref=item.get('CityRef'))
            except:
                print(item)
                continue
            item_ref =item.get('Ref')
            data_warehouse = {
                'city':city,
                'sitekey':item.get('SiteKey'),
                'description':item.get('Description'),
                'description_ru':item.get('DescriptionRu'),
                'short_address':item.get('ShortAddress'),
                'short_address_ru':item.get('ShortAddressRu'),
                'number_warehouse':item.get('Number'),
            }
            DeliveryWarehousesNP.objects.update_or_create(
                ref_warehouse=item_ref,
                defaults = data_warehouse
            )


def update_c():
    link = 'https://api.novaposhta.ua/v2.0/json/'
    headers = {'Content-Type':'application/json',}
    data = (
        '{"modelName": "Address",'
        '"calledMethod": "getCities",'
        f'"apiKey": "{os.environ.get("TOKEN_NP")}"}}'
    )
    req = requests.post(link, data=data, headers=headers)
    responce = req.json()
    cnt = 0
    if responce.get('success'):
        for item in responce['data']:
            cnt+=1
            print(cnt)
            city_ua = item['Description']
            data_city = {
                'city':item['DescriptionRu'],
                'city_ref':item['Ref'],
                'cityID':item['CityID'],
                'region_ua':item['AreaDescription'],
                'region':item['AreaDescriptionRu'],
            }
            DeliveryCitiesNP.objects.update_or_create(city_ua=city_ua, defaults=data_city)