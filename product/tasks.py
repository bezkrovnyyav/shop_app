from shop.celery import app
from product import services, parser_rozetka


@app.task
def edit_price_in_category(lst_cats, type_edit, value_edit, is_edit_old_price):
    services.ProductServices.edit_price_products(
            lst_cats=lst_cats,
            type_edit = type_edit, 
            value_edit = value_edit, 
            is_edit_old_price = is_edit_old_price
    )


@app.task
def import_from_gsheets(link):
    services.ImportSheet.import_from_gsheets(link)


@app.task
def parser_rozetka(id_cat):
    parser_rozetka.get_all_ids_goods(id_cat)