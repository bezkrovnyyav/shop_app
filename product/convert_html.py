def viewed_products(data):
    data = dict(reversed(list(data.items())))
    responce_html = ''
    for i in data.values():
        responce_html += (
            f'<div class="card" style="width: 18rem;">'
            f'<div class="card-body">'
            f'<h5 class="card-title">{i["title"]}</h5>'
            f'<p class="card-text">{i.get("desc")}</p>'
            f'<a href="/shop/product/{i.get("id")}" class="btn btn-primary">open page</a></div></div>'
            
        )
    return responce_html


def list_products(data):
    responce_html = ''
    for product in data:
        responce_html += (
            f'<div class="card mb-3" style="flex:25%">'
            f'<div class="card-body">'
            f'<h5 class="card-title"><a href="/shop/product/{product.id}">{product.title}</a></h5>'
            f'<p class="card-text">{product.price}</p>'
            f'<input type="number" step="1" min=1 name="cnt" start="1" value="1" id="cnt_product_{product.id}">'
            f'<span class="btn_basket_{product.id}"><button type="submit" onclick="add2basket({product.id})" id="btn_add2basket">Добавить в корзину</button></span>'
            '</div></div>'            
        )
    return responce_html


def pagination(item, func='spage'):
    html_result = ''
    html_result += '<span class="step-links">'
    if item.has_previous():  
         html_result += f'<a href="#" onclick="{func}({item.previous_page_number()})">Previous</a>'
    
    html_result+='<span class="current">'
    html_result+=f'Page {item.number} of {item.paginator.num_pages}.'  
    html_result+='</span>'  
    if item.has_next():
        html_result+=f'<a href="#" onclick="{func}({item.next_page_number()})">Next</a>'  
    html_result+='</span>'
    return html_result


def my_wishlist(data):
    responce_html = ''
    for item in data:
        product = item.product
        responce_html += (
            f'<div class="card" style="flex:25%">'
            f'<div class="card-body">'
            f'<h5 class="card-title"><a href="/shop/product/{product.id}">{product.title}</a></h5>'
            f'<p class="card-text">{product.price}</p>'
            f'<button type="button" class="btn btn-primary" onclick="wishlist({product.id}, \'del_for_wishlist\')" id="btn_wishlist">Удалить из вишлиста</button>'
            f'<input type="number" step="1" min=1 name="cnt" start="1" value="1" id="cnt_product_{product.id}">'
            f'<span class="btn_basket_{product.id}"><button type="submit" onclick="add2basket({product.id})" id="btn_add2basket">Добавить в корзину</button></span>'
            '</div></div>'            
        )
    return responce_html


def recommend_products(data):
    responce_html = ''
    for i in data:
        responce_html += (
            f'<div class="card" style="width: 18rem;">'
            f'<div class="card-body">'
            f'<h5 class="card-title">{i.title}</h5>'
            f'<p class="card-text">{i.desc}</p>'
            f'<a href="/shop/product/{i.id}" class="btn btn-primary">open page</a></div></div>'
        )
    return responce_html


def buy_together(data):
    responce_html = ''
    for i in data:
        responce_html += (
            f'<div class="card" style="width: 18rem;">'
            f'<div class="card-body">'
            f'<h5 class="card-title">{i["product__title"]}</h5>'
            f'<p class="card-text">Купили вместе {i["all_qty"]} раз</p>'
            f'<a href="/shop/product/{i["product"]}" class="btn btn-primary">open page</a></div></div>'
        )
    return responce_html


def select_rating_product(id, select_rating):
    html_result = ''
    html_result+=f'<select name="rating_product" id="rating_product">'
    html_result+=f'<option value="0">Выбрать</option>'
    for i in range(1, 11):
        select = 'selected' if select_rating == i else ''
        html_result += f'<option value={i} {select}>{i}</option>'
    html_result += '</select>'
    html_result+=f'<button onclick="edit_ratign({id})">Проголосовать</button>'
    return html_result


def delivery_np(data):
    html_result = ''
    html_result=f'<br><span class=\'desc_info\'><select id=\'delivery_novaposhta\' class = \'{data.get("type")}_delivery\'>'
    for i in data['select']:
        html_result += f'<option value="{i}">{i}</option>'
    html_result += '</select>'
    if data.get('type') == 'region_novaposhta':
        html_result+=f'<button type=\'button\' class = \'{data.get("type")}_delivery\' onclick="select_delivery(\'region\', \'novaposhta\')">Выбрать</button></span>'
    if data.get('type') == 'city_novaposhta':
        html_result+=f'<button type=\'button\' class = \'{data.get("type")}_delivery\' onclick="select_delivery(\'city\', \'novaposhta\')">Выбрать</button></span>'
    if data.get('type') == 'warehouses_novaposhta':
        html_result+=f'<button type=\'button\' class = \'{data.get("type")}_delivery\' onclick="select_delivery(\'warehouses\', \'novaposhta\', \'{data.get("ref")}\')">Выбрать</button></span>'

    return html_result