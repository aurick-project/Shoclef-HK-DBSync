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
from hk.scripts.livestreams import *
from hk.scripts.orders import *
from hk.scripts.payments import *


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


def check_products(request):
    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]
    m_products = mongo_db['products'].find()
    duplicated = {}
    duplicated_ids = []
    missing_assets = {}
    missing_shipping_box = []
    missing_sellerinfo = []
    missing_customcarrier = []
    missing_customcarrier_value = []
    image_formats = ("image/png", "image/jpeg", "image/jpg")
    prod_cnt = 0
    for mp in m_products:
        prod_cnt += 1
        print(prod_cnt, mp['_id'])
        missing_assets_for_one = []
        mp_assets = mp['assets']
        if mp_assets:
            for mp_asset in mp_assets:
                ma = mongo_db['assets'].find_one({'_id': mp_asset})
                if ma:
                    # response = requests.head(ma['url'])
                    # if response.headers['content-type'] not in image_formats:
                    #     missing_assets_for_one.append({'state': 'uploaded but not available', 'id': mp_asset})
                    continue
                else:
                    missing_assets_for_one.append({'state': 'not exist', 'id': mp_asset})
        if missing_assets_for_one:
            missing_assets[mp['_id']] = missing_assets_for_one
        if mp['_id'] in duplicated_ids:
            continue
        same_prod = mongo_db['products'].find({'title': mp['title']})
        if same_prod.count() > 1:
            duplicated[mp['_id']] = []
            for sp in same_prod:
                duplicated_ids.append(sp['_id'])
                if sp['_id'] != mp['_id']:
                    duplicated[mp['_id']].append(sp['_id'])
    print('-' * 50)
    print('duplicated')
    pprint(duplicated)

    print('-' * 50)
    print('missing assets')
    pprint(missing_assets)

    return HttpResponse('OK')


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
    elif title == 'users_delete':
        start_sync_users_delete()
    elif title == 'livestreams':
        start_sync_livestreams()
    elif title == 'livestreams_delete':
        start_sync_livestreams_delete()
    elif title == 'orders':
        start_sync_orders()
    elif title == 'orders_delete':
        start_sync_orders_delete()
    elif title == 'payments':
        start_sync_payments()
    elif title == 'payments_delete':
        start_sync_payments_delete()
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
        # page += 1
        if woo_prods:
            delete_ids = []
            for wc in woo_prods:
                delete_ids.append(wc['id'])
            delete_product_from_woocommerce(wapi, delete_ids)
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

    users = mongo_db['users'].find().limit(10)
    for user in users:
        print('-' * 30)
        # check if user exist in log
        exist_user = get_user_from_log(user['_id'])
        if exist_user:
            print('user exist in woocmmerce %s' % exist_user.woo_id)
        else:
            user_add(mongo_db, wapi, user)

    save_status('users', 0)


def start_sync_users_delete():
    print('start syncing users')
    print('-' * 30)
    print('get users from mongo')
    wapi = woo_api(woocommerce)

    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]

    users = mongo_db['users'].find()
    for user in users:
        pprint(user)

    save_status('users_delete', 0)


def start_sync_livestreams():
    print('start syncing livestreams')
    print('-' * 30)
    print('get livestreams from mongo')
    wapi = woo_api(woocommerce)

    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]

    mysql_conn = mysql_db_connect(mysql)
    mysql_cursor = mysql_conn.cursor(dictionary=True, buffered=True)

    livestreams = mongo_db['livestreams'].find()
    for livestream in livestreams:
        print('-' * 30)
        print('livestream', livestream['_id'])
        add_livestream(wapi, mongo_db, mysql_conn, mysql_cursor, livestream)
    mysql_db_close(mysql_conn, mysql_cursor)
    save_status('livestreams', 0)


def start_sync_livestreams_delete():
    print('start syncing livestreams_delete')
    print('-' * 30)
    print('get users from mongo')
    wapi = woo_api(woocommerce)

    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]

    mysql_conn = mysql_db_connect(mysql)
    mysql_cursor = mysql_conn.cursor(dictionary=True, buffered=True)
    woo_livestreams = mysql_select_table(mysql_cursor, 'wp_posts', where='post_type="livestream"')
    if woo_livestreams:
        for wl in woo_livestreams:
            delete_livestream_from_db(mysql_conn, mysql_cursor, wl['ID'])

    mysql_db_close(mysql_conn, mysql_cursor)

    save_status('livestreams_delete', 0)


def start_sync_orders():
    print('start syncing orders')
    print('-' * 30)
    print('get users from mongo')
    wapi = woo_api(woocommerce)

    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]

    users = mongo_db['users'].find()
    for user in users:
        pprint(user)

    save_status('orders', 0)


def start_sync_orders_delete():
    print('start syncing orders_delete')
    print('-' * 30)
    print('get users from mongo')
    wapi = woo_api(woocommerce)

    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]

    users = mongo_db['users'].find()
    for user in users:
        pprint(user)

    save_status('orders_delete', 0)


def start_sync_payments():
    print('start syncing payments')
    print('-' * 30)
    print('get users from mongo')
    wapi = woo_api(woocommerce)

    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]

    users = mongo_db['users'].find()
    for user in users:
        pprint(user)

    save_status('payments', 0)


def start_sync_payments_delete():
    print('start syncing payments_delete')
    print('-' * 30)
    print('get users from mongo')
    wapi = woo_api(woocommerce)

    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]

    users = mongo_db['users'].find()
    for user in users:
        pprint(user)

    save_status('payments_delete', 0)
