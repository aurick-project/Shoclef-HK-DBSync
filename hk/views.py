import json
from pprint import pprint
from django.http import HttpResponse
from django.shortcuts import redirect, render
from hk.mysql_connect import *
from hk.mongo_connect import *
from hk.settings import *
from hk.scripts.products import *
from hk.scripts.categories import *
from hk.scripts.tags import *
from hk.scripts.users import *


# Create your views here.
def index(request):
    content = {
        'woo_connect':       False,
        'mongo_connect':     False,
        'mysql_connect':     False,
        'mysql_log_connect': False,
        'current_state':     ''
    }
    wapi = woo_api(woocommerce)
    if wapi:
        content['woo_connect'] = True

    mapi = mongo_connect(mongo['url'])
    if mapi:
        content['mongo_connect'] = True

    mysql_db = mysql_db_connect(mysql)
    if mysql_db:
        content['mysql_connect'] = True
        mysql_db_close(mysql_db)
    current_states = get_status()
    if current_states:
        for cs in current_states:
            content['current_state'] = cs.title
    return render(request, 'index.html', content)


def set_status(request, title, state):
    print('-' * 30)
    print('Set status %s %s' % (title, state))
    save_status(title, state)
    return redirect(index)


def start_sync(request, title):
    print(title)
    if title == 'products':
        start_sync_products()
    elif title == 'products_delete':
        start_sync_products_delete()
    elif title == 'categories':
        start_sync_categories()
    elif title == 'categories_delete':
        start_sync_categories_delete()
    elif title == 'users':
        start_sync_users()
    return HttpResponse('Hello')


def start_sync_categories():
    print('start syncing categories')
    print('-' * 30)
    print('get products from mongo')
    wapi = woo_api(woocommerce)

    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]
    m_categories = mongo_db['productcategories'].find().limit(10)
    for mc in m_categories:
        woo_cat_id = add_category(mongo_db, wapi, mc['_id'])
        print('add cateogry %s %s' % (mc['_id'], woo_cat_id))
    save_status('categories', 0)


def start_sync_categories_delete():
    print('start syncing category delete')
    print('-' * 30)
    print('get categories from db')
    wapi = woo_api(woocommerce)
    page = 1
    per_page = 100
    while True:
        sync_statues = get_status('categories_delete')
        if sync_statues.state == 0:
            print('-' * 30)
            print('Break syncing...')
            break
        woo_cats = woo_categories(wapi, page, per_page)
        page += 1
        if woo_cats:
            for wc in woo_cats:
                sync_statues = get_status('categories_delete')
                if sync_statues.state == 0:
                    print('-' * 30)
                    print('Break syncing...')
                    break
                delete_cat_from_woocommerce(wapi, wc['id'])
        else:
            break
    save_status('categories_delete', 0)


def start_sync_products():
    print('start syncing products')
    print('-' * 30)
    print('get products from mongo')

    # get currency convert rate
    cc_res = []
    try:
        cc_req_res = requests.get('http://www.floatrates.com/daily/usd.json')
        cc_res = json.loads(cc_req_res.content)
    except:
        print('get currency convert reate failed')
        pass

    wapi = woo_api(woocommerce)

    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]
    m_products = mongo_db['products'].find().limit(10)
    for mp in m_products:
        sync_statues = get_status('products')
        if sync_statues.state == 0:
            print('-' * 30)
            print('Break syncing...')
            break
        print('-' * 30)
        # pprint(mp)
        # check if already exist in log
        exist_in_log = get_product_from_log(mongo_id=mp['_id'])
        if exist_in_log:
            print('product exist in log db')
            # check if exist in woocommerce
            exist_in_woo = woo_product_one(wapi, woo_id=exist_in_log.woo_id)
            if exist_in_woo:
                print('product exist in woocommerce')
                woo_prod_id = exist_in_woo['id']
                # check all info same with mongo and woocommerce product
            else:
                woo_prod_id = add_product(mongo_db, wapi, mp, cc_res)
        else:
            print('product not exist in log db')
            # check if exist in woocommerce
            exist_in_woo = woo_product_one(wapi, sku=mp['_id'])
            if exist_in_woo:
                print('exist in woocommerce')
                woo_cat_id = add_category(mapi, wapi, mp['category'])
                save_product_to_log(mongo_id=mp['_id'], woo_id=exist_in_woo[0]['id'], category=woo_cat_id)
                woo_prod_id = exist_in_woo[0]['id']
            else:
                print('product not exist in woocommerce')
                # insert to woocommerce
                woo_prod_id = add_product(mongo_db, wapi, mp, cc_res)
        print('product insert success %s' % woo_prod_id)
    save_status('products', 0)


def start_sync_products_delete():
    print('start syncing products delete')
    print('-' * 30)
    print('get products delete syncing status from db')
    wapi = woo_api(woocommerce)
    page = 1
    per_page = 100
    while True:
        sync_statues = get_status('products_delete')
        if sync_statues.state == 0:
            print('-' * 30)
            print('1 Break syncing...')
            break
        woo_prods = woo_products(wapi, page, per_page)
        page += 1
        if woo_prods:
            for wc in woo_prods:
                sync_statues = get_status('products_delete')
                if sync_statues.state == 0:
                    print('-' * 30)
                    print('2 Break syncing...')
                    break
                delete_product_from_woocommerce(wapi, wc['id'])
        else:
            break
    save_status('products_delete', 0)


def start_sync_users():
    print('start syncing users')
    print('-' * 30)
    print('get users from mongo')
    wapi = woo_api(woocommerce)

    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]

    users = mongo_db['users'].find()
    for user in users:
        pprint(user)

    save_status('users', 0)
