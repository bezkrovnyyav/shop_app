from accounts.models import *
from product import models as models_shop
import requests
import json
from dotenv import load_dotenv
load_dotenv()
import os
import re


TG_TOKEN = os.environ.get('TG_TOKEN')


def geo_ip_info(ip_address):
    req = requests.get(f'http://ipwhois.app/json/{ip_address}').json()
    response = {}
    if req.get('success'):
        response['country'] = req.get('country') if req.get('country') else ''
        response['region'] = req.get('region') if req.get('region') else ''
        response['city'] = req.get('city') if req.get('city') else ''
    return response


def subscribe_answer_support(id_user, text_answer):
    try:
        user = Subscribe.objects.get(user_id = id_user, is_answer_support = True)
    except Subscribe.DoesNotExist:
        return False
    
    message = f'Вы получили ответ на ваше обращение: \n\n{text_answer}'
    id_tg = user.user.id_tg
    link = f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={id_tg}&parse_mode=HTML&text={message[:200]}'
    req = requests.get(link)


def subscribe_create_order(id_user, id_order, url_order):
    try:
        user = Subscribe.objects.get(user_id = id_user, is_create_order = True)
    except Subscribe.DoesNotExist:
        return False
    
    message = f'Вы оформили заказ с ID {id_order}\nСсылка на заказ: {os.environ.get("LINK_SITE")}{url_order}'
    id_tg = user.user.id_tg
    link = f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={id_tg}&parse_mode=HTML&text={message}'
    req = requests.get(link)
    print(link)
    print(req.text)


def subscribe_authorization(id_user, session_key, ip):
    try:
        user = Subscribe.objects.get(user_id = id_user, is_authorization = True)
    except Subscribe.DoesNotExist:
        return False

    ip_info = geo_ip_info(ip)
    str_ip_info = '/'.join(ip_info.values())
    message = f'В ваш аккаунт был выполнен вход с IP-адреса {ip} ({str_ip_info})\nЕсли это были не вы - нажмите кнопку ниже.'
    id_tg = user.user.id_tg
    link = f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={id_tg}&parse_mode=HTML&text={message}&reply_markup={{"inline_keyboard":[[{{"text":"Закрыть сеанс","callback_data":"type_action:close_session:{session_key}"}}]]}}'
    req = requests.get(link)


def promo_replace_username(user = None):
    if user.username:
        return user.username
    else:
        return user.email


def promo_replace_oncepromo():
    promo = models_shop.Promocode.generate_new_promocode()
    if promo:
        return promo[0]
    return None


def promo_replace_balance(user = None):
    return str(round(user.balance, 2))


def promo_replace_product(element):
    lst = element.split('|')
    while len(lst) <= 2:
        lst.append('')
    product = {'id':lst[1], 'type':lst[2]}
    try:
        product_info = models_shop.Product.objects.get(pk = product['id'])
        if product['type'] == 'name':
            return product_info.title
        elif product['type'] == 'oldprice':
            return str(product_info.old_price)
        elif product['type'] == 'price':
            return str(product_info.price)
        elif product['type'] == 'link':
            return f'{os.environ.get("LINK_SITE")}{product_info.get_absolute_url()}'
    except models_shop.Product.DoesNotExist:
        return None


def replace_text(text, user = None):
    origin_text = text
    r = re.findall(r'(\{\% .*? \%\})', origin_text)
    for i in r:
        el = re.search(r'{% (.*?) %}', i)
        if el:
            element = el.group(1)
            name_element = element.split('|')[0]
            if name_element == 'username':
                repl = promo_replace_username(user = user)
            elif name_element == 'oncepromo':
                repl = promo_replace_oncepromo()  
            elif name_element == 'product':
                repl = promo_replace_product(element)
            elif name_element == 'balance':
                repl = promo_replace_balance(user = user)
            if not repl:
                repl = ''
            origin_text = origin_text.replace(i, repl)
            
    return origin_text


def subscribe_promo(text_msg):
    users = Subscribe.objects.filter(is_promo = True)
    for user in users:
        id_tg = user.user.id_tg
        message = replace_text(text_msg, user = user.user)
        
        link = f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={id_tg}&parse_mode=HTML&text={message[:200]}'
        req = requests.get(link)
        print(req.json())
    
    
def subscribe_get_file_in_order(id_order):
    try:
        order = models_shop.Order.objects.get(pk = id_order)
        user = Subscribe.objects.get(user_id = order.user, is_get_digit_file = True)
    except (models_shop.Order.DoesNotExist, Subscribe.DoesNotExist):
        return False
    all_files = order.orderitem_set.all()
    for item in all_files:
        try:
            product = models_shop.Product.objects.get(pk=item.product.id)
        except models_shop.Product.DoesNotExist:
            return False
    
        if product.type_product == 'file':
            token_file = product.filetelegram_set.all()
            file_id = ''
            link = f'https://api.telegram.org/bot{TG_TOKEN}/sendDocument?chat_id={user.user.id_tg}&parse_mode=HTML'
            if token_file:
                file_id = token_file.first().id_file
                files = {'document':file_id}
                req = requests.post(link, data=files)
            else:
                files = {'document':(product.file_digit.name, product.file_digit)}
                req = requests.post(link, files = files)
                if req.status_code == 200:
                    new_token = req.json()
                    new_token = new_token['result']['document']['file_id']
                    models_shop.FileTelegram.objects.update_or_create(
                        product = product,
                        defaults = {'id_file':new_token}
                    )


def subscribe_edit_price(lst, name, new_price):
    message = f'Изменилась цена на товар {name}\nНовая цена - {new_price}'
    for id_tg in lst:
        link = f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={id_tg}&parse_mode=HTML&text={message[:200]}'
        req = requests.get(link)


def subscribe_active_product(lst, product_name, price, items):
    message = f'Товар "{product_name}" снова в наличии! Успей купить по цене {price}'
    for id_tg in lst:
        link = f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={id_tg}&parse_mode=HTML&text={message[:200]}'
        req = requests.get(link)
        print(req.json())
    all_items = models_shop.SubActivateProduct.objects.filter(pk__in = items)
    all_items.delete()