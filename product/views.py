from django.shortcuts import render, HttpResponseRedirect, get_object_or_404, redirect, HttpResponse
from product.models import *
from django.urls import reverse
from django.forms.models import model_to_dict
from product import forms
from accounts import models
from product import services
import json
import requests
import datetime
from dotenv import load_dotenv
from product import convert_html
load_dotenv()
import os
from django.db.models import Sum
import re
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  
from django.contrib.auth.models import Group
from product import tasks
from accounts import tasks as acc_tasks


def all_links(request):
    return render(request, 'product/all_links.html')


def shop_main_page(request):
    categories = Categories.objects.all()
    return render(request, 'product/main_page.html', context={'category':categories})


def category_page(request, pk):
    category = Product.objects.filter(cid=pk)
    return render(request, 'product/category_page.html', context={'products':category})


def all_product_page(request):
    all_product = Product.objects.all().order_by('-date_add')
    paginator = Paginator(all_product, 20)
    page = 1
    if request.method == 'POST':
        responce = {}
        page=request.POST.get('page', 1)
        try:  
            products = paginator.page(page)  
        except PageNotAnInteger:  
            # Если страница не является целым числом, поставим первую страницу  
            products = paginator.page(1)  
        except EmptyPage:  
            # Если страница больше максимальной, доставить последнюю страницу результатов  
            products = paginator.page(paginator.num_pages)
        responce['success'] = convert_html.list_products(products)
        responce['pagination'] = convert_html.pagination(products)
        return HttpResponse(json.dumps(responce), content_type='applicaion/json')
    else:
        products = paginator.page(page) 
    all_product_html = convert_html.list_products(products)
    pagination = convert_html.pagination(products)
    return render(request, 'product/all_product_page.html', context={'pagination':pagination, 'products':all_product_html, 'page':page})


def product_page(request, pk):
    context = {}
    viewed_products = request.session.get('viewed_products', {})
    product = get_object_or_404(Product, pk=pk)
    viewed_products.pop(str(product.id), None)
    if len(viewed_products) >= 6: del viewed_products[next(iter(viewed_products))]
    viewed_products_html = convert_html.viewed_products(viewed_products)
    context['product'] = product
    viewed_products[str(product.id)] = {'id':product.id, 'title':product.title, 'price':product.price, 'desc':product.desc}
    request.session['viewed_products'] = viewed_products
    context['viewed_products'] = viewed_products_html
    if request.user.is_authenticated:
        try:
            context['is_wishlist']=product.wishlist_set.get(user = request.user)
        except Wishlist.DoesNotExist:
            context['is_wishlist'] = False
        try:
            context['is_sub_edit_price']=product.subeditprice_set.get(user = request.user)
        except SubEditPrice.DoesNotExist:
            context['is_sub_edit_price']=False
        try:
            context['is_sub_active_product'] = product.subactivateproduct_set.get(user = request.user)
        except SubActivateProduct.DoesNotExist:
            context['is_sub_active_product'] = False
    lst_ids_cats = list(product.cid.values_list('id', flat=True))
    rec_f1 = Product.objects.exclude(pk=product.pk).filter(is_recommend=True, cid__in=lst_ids_cats).order_by('?')[:1]
    rec_f2 = Product.objects.exclude(pk=product.pk).filter(
        cid__in=lst_ids_cats, 
        price__gt=product.price*0.7, 
        price__lt=product.price*1.3).order_by('?')[:5]
    recommend_products = rec_f1|rec_f2
    recommend_products = recommend_products[:5]
    context['rating_product'] = product.rating
    if request.user.is_authenticated:
        select_rating = product.select_rating(user=request.user)
        context['select_rating']=convert_html.select_rating_product(product.id, select_rating)
    context['recommend_pr'] = convert_html.recommend_products(recommend_products)
    
    ### кусок гкода для блока "с этим товаром так же покупают". я понимаю, что это гкод и мне стыдно за него
    ### но оно работает))))
    all_item = OrderItem.objects.filter(product = product) 
    lst_all_order = []
    for i in all_item:
        lst_all_order.append(i.order)
    
    all_orderitem_with_product = OrderItem.objects.filter(order__in = lst_all_order).exclude(product=product)
    buy_together = all_orderitem_with_product.values(
        'product', 'product__title'
        ).annotate(all_qty = Sum('qty')).order_by('-all_qty')[:5]
    context['buy_together'] = convert_html.buy_together(buy_together)

    return render(request, 'product/product_page.html', context)

def select_curr(request):
    if request.method == 'POST':
        link = request.META.get('HTTP_REFERER')
        request.session['curr_id'] = request.POST.get('all_currency')
        return HttpResponseRedirect(link)

def basket(request):
    if request.method == 'POST':
        
        basket = services.Basket.get_basket(request.user.id) if request.user.is_authenticated else request.session.get('basket', {})
        type_basket = request.POST.get('type')
        product_id = request.POST.get('id')
        check_promo = request.POST.get('promocode')
        data_response={}
        product_cnt = request.POST.get('cnt', 1)
        type_add2basket = request.POST.get('type_basket', 'add')
        if int(product_cnt) < 1:
            data_response={'error':'Минимальное количество - 1'}
            return HttpResponse(json.dumps(data_response), content_type = 'application/json')


        product_cnt = 1 if not product_cnt else product_cnt   
        if type_basket == 'add':
            basket = services.Basket.add2basket(basket, product_id, product_cnt, user_id=request.user.id, _type = type_add2basket)
            if type_add2basket == 'add':
                data_response = {'success': f'Добавлено в корзину {product_cnt} товаров'}
            elif type_add2basket == 'edit':
                total_cost = round(sum([i['qty'] * i['price'] for i in basket.values()]), 2)
                total_cost_resp = f'{total_cost *  request.session["rate_curr"]} {request.session["disp_curr"]}'
                data_response = {'success':True, 'total_cost':total_cost_resp}
                
        elif type_basket == 'del':
            basket = services.Basket.del2basket(basket, product_id, request.user.id)
            html_result = ""
            count_items = 1
            for product_val in basket.values():
                id_product = product_val['id']
                html_result += f'<tr><th scope="row">{count_items}</th>'
                html_result += f'<td><a href=\'{reverse("product_page", kwargs={"pk":id_product})}\'">{product_val["title"]}</a></td>'
                html_result += f'<td>{product_val["price"] * request.session["rate_curr"]}</td>'
                html_result += f'<td><input onchange = "edit_qty({id_product}, this.value)" type="number" value="{product_val["qty"]}"></td>'
                html_result += f'<td><button type=\'submit\' onclick="del_basket({id_product})">X</button></td>'
                html_result += '</tr>'
                count_items+=1
                    
            html_result += ''
            data_response = {'success':'Удалено', 'responce':html_result}
        elif check_promo:
            promo = Promocode.objects.filter(code = check_promo).first()
            if promo:
                sum_discount = promo.get_sum_discount(basket['full_sum_basket'])
                if sum_discount:
                    total_sum = round((basket['full_sum_basket'] + sum_discount)*request.session['rate_curr'], 2)
                    data_response = {'success':total_sum}
                else:
                    data_response={'error':'Промо не найден.'}
            else:
                data_response={'error':'Промо не найден.'}
            
        request.session['basket'] = basket

        return HttpResponse(json.dumps(data_response), content_type = 'application/json')


def checkout_page(request):
    basket = services.Basket.get_basket(request.user.id) if request.user.is_authenticated else request.session.get('basket', {})
    total_cost = sum([i['qty'] * i['price'] for i in basket.values()])
    delivery = Delivery.objects.all()
    if request.method == 'POST':
        data = request.POST.copy()
        responce = {}
        id_delivery = data.get('delivery')
        order_delivery = Delivery.objects.get(pk=id_delivery)
        order_currency = Currency.objects.get(code = request.session.get('curr_id', 'UAH'))
        promocode = data.get('promo_code')
        is_promo = False
        if promocode:
            is_promo = Promocode.is_promo(data.get('promo_code'))
            if is_promo:
                data['promo'] = Promocode.objects.get(code = data['promo_code'])
        data['user'] = request.user if request.user.is_authenticated else ''
        data['currency'] = order_currency
        data['rate_currency'] = order_currency.rate
        data['delivery_method'] = order_delivery
        create_order = forms.OrderForm(data)
        print(create_order.errors)

        if create_order.is_valid() and basket:
            new_order = create_order.save()
            if data.get('promo'):
                if data.get('promo').type_promo == 'onceuse':
                    data.get('promo').status = False
                    data.get('promo').save()
            if request.user:
                acc_tasks.send_create_order.delay(request.user.id, new_order.id, new_order.get_absolute_url())
            for good in basket.values():
                item = {
                    'product':Product.objects.get(pk=good['id']),
                    'order':new_order,
                    'qty':good['qty'],
                }
                OrderItem.add_item(item)
                new_order.recalc_order()
            responce = {'success':True, 'msg':f'Заказ оформлен.<br><a href="{reverse("invoice_page", kwargs={"pk":new_order.id})}">Перейти на страницу заказа</a>'}
        else:
            responce = {'success':False, 'msg':create_order.errors}

        return HttpResponse(json.dumps(responce), content_type='applicaion/json')
    
        #return redirect('invoice_page', new_order.id)  

    return render(request, 'product/checkout_page.html', context={'products':basket, 'total_cost':total_cost, 'all_delivery':delivery})


def all_invoices(request):
    """ страница со всеми заказами """
    template = 'product/all_invoices.html'
    context = {}
    filter_order = {}
    date_default = {}
    context['all_couriers'] = Group.objects.get(name='Courier').user_set.all()
    if request.method == 'POST':
        data = request.POST
        if data.get('filter'):
            filter_order = services.OrderServise.filter_order(data)
    context['filter'] = filter_order
    date_default = {
        'date_start':filter_order.pop('date_start', ''),
        'date_end':filter_order.pop('date_end', ''),
    }
    all_invoices = Order.objects.filter(**filter_order).order_by('-pk')
    all_status = forms.ChangeStatusOrder()
    context['all_invoices'] = all_invoices
    context['all_status'] = all_status
    context['filter'].update(date_default)
    return render(request, template, context=context)


def change_invoice(request):
    """ смена статуса заказа """
    if request.method == 'POST':
        link = request.META.get('HTTP_REFERER')
        Order.change_status(request.POST.get('id_order'), request.POST.get('status'))
        return HttpResponseRedirect(link)    


def get_invoice(request, pk):
    template = 'product/invoice_page.html'
    context = {}
    order = get_object_or_404(Order, pk=pk)
    goods = order.orderitem_set.all()
    digital_links = {}
    if order.status == 'paid':
        for good in goods:
            product_in_inv = get_object_or_404(Product, pk = good.id_good)
            type_good = product_in_inv.type_product
            if type_good == 'file':
                link_product_file = product_in_inv.file_digit.url
                digital_links[good.title_good] = link_product_file
    if request.user.is_authenticated and order.user:
        if request.user.id == order.user.id:
            user_balance = order.user.balance
            if user_balance >= order.total_amount and order.status != 'paid':
                context['pay'] = True

    if order.is_paid and request.user.has_perm('product.change_status'):
        context['cancel_order'] = True

    if request.method == 'POST':
        data = request.POST
        meta = data.get('mode')
        if meta == 'pay_order':
            if context.get('pay'):
                context['pay'] = not order.payment()
        elif meta=='cancel_order' and context.get('cancel_order'):
                context['cancel_order'] = not order.cancel_order()
                context['pay'] = True

    context['order'] = order
    context['goods'] = goods
    context['digital'] = digital_links
    if order.delivery_department:
        wh_info = DeliveryWarehousesNP.objects.get(ref_warehouse = order.delivery_department)
        context['delivery_department'] = f'{wh_info.city.city}, <br>{wh_info.description_ru}'
    return render(request, template, context=context)


def edit_invoice(request, pk):
    template = 'product/invoice_edit_page.html'
    context = {}
    order = get_object_or_404(Order, pk=pk)
    goods = order.orderitem_set.all()
    context['order'] = order
    if request.method == 'POST':
        mode  = request.POST.get('mode') 
        data = request.POST
        if mode == 'edit_invoice':
            for good in goods:
                try:
                    edit_price = float(data.get(f'price_{good.id}'))
                    edit_qty = int(data.get(f'qty_{good.id}'))
                    del_good = data.get(f'del_{good.id}')
                except ValueError:
                    break
                if edit_price and edit_qty:
                    if del_good:
                        OrderItem.objects.get(pk = good.id).delete()
                        continue
                    
                    item_info={
                        'pk':good.id,
                        'price':edit_price,
                        'qty':edit_qty,
                    }
                    OrderItem.add_item(item_info)
            goods = order.orderitem_set.all()
        
        elif mode == 'add_good':
            product = get_object_or_404(Product, pk = data.get('id_good'))
            item_info = {
                'product':product,
                'order':order,
            }
            OrderItem.add_item(item_info)
        order.recalc_order()
    context['goods'] = goods
                
            
    return render(request, template, context=context)


def create_promocode(request):
    template = 'product/create_promocode_page.html'
    form = forms.CreatePromo()
    if request.method == 'POST':
        create_code = forms.CreatePromo(request.POST)
        if create_code.is_valid():
            create_code.save()
    return render(request, template, context={'form':form})


def edit_price_in_category(request):
    template = 'product/edit_price_in_category.html'
    context = {}
    categories = Categories.objects.all()
    context['categories'] = categories
    if request.method == 'POST':
        data = request.POST
        data_for_edit = services.ProductServices.data_preparation_edit_price(data)
        #products = services.ProductServices.get_all_products_in_categories(data_for_edit['lst_cats_id'])
        tasks.edit_price_in_category.delay(
            lst_cats=data_for_edit['lst_cats_id'],
            type_edit = data_for_edit['type_edit'], 
            value_edit = data_for_edit['value_edit'], 
            is_edit_old_price = data_for_edit['is_edit_old_price']
        )

    return render(request, template, context)


def export_products(request):
    template = 'product/export.html'
    context = {}
    if request.method == 'POST':
        data_response = {}
        type_file = request.POST.get('type', 'csv')
        export_file = services.ProductServices.export_to_file(type_file)
        if export_file:
            data_response['success'] = export_file            
        return HttpResponse(json.dumps(data_response), content_type = 'application/json')

    return render(request, template, context)

def import_products(request):
    template = 'product/import.html'
    context = {}
    if request.method == 'POST':
        data = request.POST
        type_import = data.get('type')
        link_price = data.get('link')
        data_response = {}
        is_valid_link = services.ImportSheet.is_correct_link(link_price)
        if type_import == 'import':
            if is_valid_link:
                tasks.import_from_gsheets.delay(link_price)
                data_response['success'] = '<b>Выполняется обработка прайса..</b>'
            else:
                data_response['error'] = 'Файл по указанной сыслке недоступен.'
        elif type_import == 'preview':
            if is_valid_link:
                lst_on_preview = services.ImportSheet.import_from_gsheets(link_price, preview=True)
                data_response['success'] = services.ImportSheet.generate_preview_to_front(lst_on_preview)
                data_response['preview'] = True
            else:
                data_response['error'] = 'Файл по указанной сыслке недоступен.'

        return HttpResponse(json.dumps(data_response), content_type = 'application/json')

    return render(request, template)


def matrix(request):
    template = 'product/matrix_page.html'
    context = {}
    all_matrix = PriceMatrix.objects.all()
    context['all_matrix'] = {}
    for matrix in all_matrix:
        matrix_imets = matrix.pricematrixitem_set.all()
        context['all_matrix'][matrix.name] = {}
        for item in matrix_imets:
            context['all_matrix'][matrix.name][f'min_{item.pk}'] = item.min_value 
            context['all_matrix'][matrix.name][f'max_{item.pk}'] = item.max_value 
            context['all_matrix'][matrix.name][f'type_{item.pk}'] = item.type_item 
            context['all_matrix'][matrix.name][f'value{item.pk}'] = item.value 
            context['all_matrix'][matrix.name]['id'] = item.pk 
    return render(request, template, context)



def wishlist(request):
    if request.method == 'POST':
        data_response = {}
        data = request.POST
        type_action = data.get('type')
        product = get_object_or_404(Product, pk = data.get('id'))
        if type_action == 'add':
            if not product.is_wishlist(request.user):
                product.add_to_wishlist(request.user)
                data_response['success'] = {'msg':'Товар добавлен в список желаний'}
            else:
                data_response['error'] = {'msg':'Товар уже в списке желаний'}
        elif type_action == 'del':
            if product.del_to_wishlist(request.user):
                data_response['success'] = {'msg':'Товар удален из списка желаний'}
            else:
                data_response['error'] = {'msg':'Товар не найден в списке желаний'}
        elif type_action=='del_for_wishlist':
            if product.del_to_wishlist(request.user):            
                wishlist = Wishlist.objects.filter(user = request.user)
                data_response['success'] = convert_html.my_wishlist(wishlist)
            else:
                data_response['error'] = {'msg':'Товар не найден в списке желаний'}
        return HttpResponse(json.dumps(data_response), content_type = 'application/json')


    elif request.method == 'GET':
        context = {}
        template = 'product/wishlist.html'
        wishlist = Wishlist.objects.filter(user = request.user)
        context['products'] = convert_html.my_wishlist(wishlist) 
        return render(request, template, context)



def subeditprice(request):
    if request.method == 'POST':
        data_response = {}
        data = request.POST
        type_action = data.get('type')
        product = get_object_or_404(Product, pk = data.get('id'))
        if type_action == 'add':
            item, create = SubEditPrice.objects.get_or_create(
                user = request.user,
                product = product,
            )
            if create:
                data_response['success'] = {'msg':'Товар добавлен в подписки'}
            else:
                data_response['error'] = {'msg':'Ты уже подписан'}
        elif type_action == 'del':
            try:
                SubEditPrice.objects.get(
                    user = request.user, 
                    product = product,
                ).delete()
                data_response['success'] = {'msg':'Подписка отменена'}
            except SubEditPrice.DoesNotExist:
                data_response['error'] = {'msg':'Товар не найден в подписках'}
        return HttpResponse(json.dumps(data_response), content_type = 'application/json')


def subactivateproduct(request):
    if request.method == 'POST':
        data_response = {}
        data = request.POST
        type_action = data.get('type')
        product = get_object_or_404(Product, pk = data.get('id'))
        if type_action == 'add':
            item, create = SubActivateProduct.objects.get_or_create(
                user = request.user,
                product = product,
            )
            if create:
                data_response['success'] = {'msg':'Мы сообщим!'}
            else:
                data_response['error'] = {'msg':'Ты уже подписан'}
        elif type_action == 'del':
            try:
                SubActivateProduct.objects.get(
                    user = request.user, 
                    product = product,
                ).delete()
                data_response['success'] = {'msg':'Подписка отменена'}
            except SubActivateProduct.DoesNotExist:
                data_response['error'] = {'msg':'Товар не найден в подписках'}
        return HttpResponse(json.dumps(data_response), content_type = 'application/json')


def rating_product(request):
    data_response = {}
    if request.method == 'POST':
        data = request.POST
        mark = int(data.get('mark', 0))
        try:
            product = Product.objects.get(pk=data.get('id'))
            if mark==0:
                try:
                    pr_delete = product.rating_product.get(user=request.user)
                    pr_delete.delete()
                    data_response['success'] = 'Оценка снята.'
                    pr_delete.recalc_rating()
                except RatingProduct.DoesNotExist:
                    data_response['error'] = 'Вы еще не голосовали.'
            else:
                product.rating_product.update_or_create(user=request.user, 
                    defaults={'value_rating':data.get('mark')})
                data_response['success'] = 'Спасибо за оценку.'
            data_response['new_avg'] = Product.objects.get(pk=data.get('id')).rating
        except Product.DoesNotExist:
            data_response['error'] = 'Некорректные параметры'
    return HttpResponse(json.dumps(data_response), content_type='application/json')


def calc_delivery(request):
    data_response = {}
    basket = services.Basket.get_basket(request.user.id) if request.user.is_authenticated else request.session.get('basket', {})
    
    if request.method == 'POST':
        data = request.POST
        total_cost = sum([i['qty'] * i['price'] for i in basket.values()])
        if data.get('delivery_id'):
            data_response = services.DeliveryFunc.calc_cost_of_delivery(data.get('delivery_id'), total_cost)
            if not data_response.get('cost') and data_response.get('cost') != 0:
                if data_response:
                    html_result = convert_html.delivery_np(data_response)
                    if html_result:
                        data_response['in_html'] = html_result
        else:
            if data.get('type_d') == 'novaposhta':
                sel_val = data.get('ref') if data.get('ref') else data.get('sel_val')
                all_values = services.DeliveryFunc.novaposhta(data.get('type_v'), sel_val, total_cost, data.get('sel_val'))
                if not all_values.get('cost'):
                    html_result = convert_html.delivery_np(all_values)
                    if html_result:
                        data_response['in_html'] = html_result
                else:
                    data_response = all_values

        #стоимость переводим в курс
        if data_response.get('cost'):
            cost_in_curr = round(data_response.get("cost") * request.session["rate_curr"], 2)
            data_response['cost'] = f'{cost_in_curr} {request.session["disp_curr"]}'

    return HttpResponse(json.dumps(data_response), content_type='application/json')



def update_cities_np(request):
    link = 'https://api.novaposhta.ua/v2.0/json/'
    headers = {'Content-Type':'application/json',}
    data = (
        '{"modelName": "Address",'
        '"calledMethod": "getCities",'
        f'"apiKey": "{os.environ.get("TOKEN_NP")}"}}'
    )
    req = requests.post(link, data=data, headers=headers)
    responce = req.json()
    if responce.get('success'):
        for item in responce['data']:
            city_ua = item['Description']
            data_city = {
                'city':item['DescriptionRu'],
                'city_ref':item['Ref'],
                'cityID':item['CityID'],
                'region_ua':item['AreaDescription'],
                'region':item['AreaDescriptionRu'],
            }
            DeliveryCitiesNP.objects.update_or_create(city_ua=city_ua, defaults=data_city)
    return HttpResponse(json.dumps(responce), content_type='application/json')



def update_warehouses_np(request):
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
    if responce.get('success'):
        for item in responce['data']:
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
            
    return HttpResponse(json.dumps(responce), content_type='application/json')


def parser_rozetka_view(request):
    if request.method == 'GET':
        template = 'product/parser_rozetka.html'
        return render(request, template)

    if request.method == 'POST':
        responce = {}
        data = request.POST
        link = data.get('link')
        search_category = re.search(r'rozetka.com.ua/.+/\D(\d+)/', link)
        if not search_category:
            responce = {'error':'Ссылка введена неверно.'}
        else:
            tasks.parser_rozetka.delay(search_category[1])
            responce = {'success':'Кража поставлена в очередь))'}

        return HttpResponse(json.dumps(responce), content_type='applicaion/json')


def select_courier(request):
    if request.method == 'POST':
        data = request.POST
        responce = {}
        print(data)
        try:
            order = Order.objects.get(pk=data['order'])
            if data.get('courier') == '0':
                order.courier = None
                order.save()
            else:
                courier = Group.objects.get(name='Courier').user_set.get(pk=data['courier'])
                order.courier = courier
                order.save()
            responce = {'success':'Сохранено'}
        except models.CustomUser.DoesNotExist:
            responce = {'error':'User not found'}
        except Order.DoesNotExist:
            responce = {'error':'Order not found'}

        return HttpResponse(json.dumps(responce), content_type='applicaion/json')


def courier_page(request):
    context = {}
    context['all_invoices'] = Order.objects.filter(courier = request.user)
    context['all_status'] = forms.ChangeStatusOrder()

    return render(request, 'product/courier_page.html', context)
