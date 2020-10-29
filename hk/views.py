import csv
import random

from bs4 import BeautifulSoup as bs
from django.http import HttpResponse
from django.shortcuts import redirect, render
from slugify import slugify

from hk.mongo_connect import *
from hk.scripts.categories import *
from hk.scripts.livestreams import *
from hk.scripts.products import *
from hk.scripts.shipping_classes import *
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
    mysql_db = mysql_db_connect(hk_mysql)
    if mysql_db:
        content['mysql_connect'] = True
        mysql_db_close(mysql_db)
    current_states = get_status()
    if current_states:
        for cs in current_states:
            content['current_state'] = cs.title
    return render(request, 'index.html', content)


def check_products(request, stop):
    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]
    skip_count = 0
    m_products = mongo_db['products'].find()
    wapi = woo_api(woocommerce)
    print('-' * 50)
    # print('delete products without images')
    # mysql_conn = mysql_db_connect(hk_mysql)
    # mysql_cursor = mysql_conn.cursor(dictionary=True, buffered=True)
    # all_products_from_log = get_product_from_log()
    # for wp in all_products_from_log:
    #     image_posts = mysql_select_table(mysql_cursor, 'wp_postmeta', where='meta_key="_thumbnail_id" and post_id=%s' % wp.woo_id, fetch='one')
    #     if image_posts in [None, '', []]:
    #         print('product %s have not image' % wp.woo_id)
    #         print('-' * 50)
    #         print('delete from woocommerce')
    #         delete_product_from_woocommerce(wapi, [wp.woo_id])
    #         print('-' * 50)
    #         print('delete from mongo')
    #         delete_query = {'_id': wp.mongo_id}
    #         if mongo_db['products'].find_one(delete_query):
    #             mongo_db['products'].delete_one(delete_query)
    #             print('product deleted from mongo db', wp.mongo_id)
    #         else:
    #             print('product is not available in mongo db', wp.mongo_id)
    #         # wp.delete()

    # mysql_db_close(mysql_conn, mysql_cursor)
    # return HttpResponse('OK')
    #
    # print('-' * 50)
    # print('delete missing assets registered on log')
    # missing_assets_log = get_missing_assets_from_log()
    # for ma in missing_assets_log:
    #     print(ma.status)
    #     if ma.status == 'Invalid' or ma.status == 'missing':
    #         print('-' * 50)
    #         print('delete from assets', ma.mongo_id)
    #         delete_query = {'_id': ma.mongo_id}
    #         if mongo_db['assets'].find_one(delete_query):
    #             mongo_db['assets'].delete_one(delete_query)s
    #             print('asset deleted from mongo db', ma.mongo_id)
    #         else:
    #             print('asset is not available in mongo db', ma.mongo_id)
    #         print('delete from products')
    #         if ma.category == 'product':
    #             if ma.parent != '':
    #                 m_product = mongo_db['products'].find_one({'_id': ma.parent})
    #                 if m_product:
    #                     if m_product['assets']:
    #                         m_product_asset_new = []
    #                         for product_asset in m_product['assets']:
    #                             if product_asset != ma.mongo_id:
    #                                 m_product_asset_new.append(product_asset)
    #                         print('update product assets without invalid asset', m_product['_id'], ma.mongo_id)
    #                         update_query = {'_id': m_product['_id']}
    #                         mongo_db['products'].update_one(update_query, {'$set': {'assets': m_product_asset_new}})
    #             else:
    #                 for m_product in m_products:
    #                     if m_product['assets']:
    #                         m_product_asset_new = []
    #                         if ma.mongo_id in m_product['assets']:
    #                             for product_asset in m_product['assets']:
    #                                 if product_asset != ma.mongo_id:
    #                                     m_product_asset_new.append(product_asset)
    #                             print('update product assets without invalid asset', m_product['_id'], ma.mongo_id)
    #                             update_query = {'_id': m_product['_id']}
    #                             mongo_db['products'].update_one(update_query, {'$set': {'assets': m_product_asset_new}})
    #     elif ma.status == 'duplicate':
    #         print('delete duplicated product')
    #         mongo_db['products'].delete_one({'_id': ma.mongo_id})

    # m_products = mongo_db['products'].find()
    duplicated = {}
    duplicated_ids = []
    image_formats = ("image/png", "image/jpeg", "image/jpg")
    prod_cnt = skip_count
    total_prod_cnt = m_products.count(True) + skip_count
    for mp in m_products:
        if stop == 1:
            break
        prod_cnt += 1
        print("product %s/%s -- %s" % (prod_cnt, total_prod_cnt, mp['_id']))
        if not mp['assets']:
            print('|---delete product have no assets')
            mongo_db['products'].delete_one({'_id': mp['_id']})
    #     missing_assets_for_one = []
    # mp_assets = mp['assets']
    # asset_cnt = 0
    # assets_count = len(mp_assets)
    # if mp_assets:
    #     for mp_asset in mp_assets:
    #         asset_cnt += 1
    #         ma = mongo_db['assets'].find_one({'_id': mp_asset})
    #         if ma:
    #             try:
    #                 response = requests.get(ma['url'])
    #                 if response.status_code != 200:
    #                     # print('|----asset %s/%s -- %s | OK' % (asset_cnt, assets_count, mp_asset))
    #                     print('|----asset %s/%s -- %s | invalid' % (asset_cnt, assets_count, mp_asset))
    #                     invalid_asset_to_log = InvalidAssets(mongo_id=ma['_id'], parent=mp['_id'], category='product')
    #                     invalid_asset_to_log.save()
    #             except Exception as e:
    #                 print(e)
    #         else:
    #             print('|----asset %s/%s -- %s | Not exist' % (asset_cnt, assets_count, mp_asset))
    #             invalid_asset_to_log = InvalidAssets(mongo_id=mp_asset, parent=mp['_id'], category='product')
    #             invalid_asset_to_log.save()

    # if mp['_id'] in duplicated_ids:
    #     continue
    # same_prod = mongo_db['products'].find({'title': mp['title'], 'price': mp['price']})
    # if same_prod.count() > 1:
    #     duplicated[mp['_id']] = []
    #     for sp in same_prod:
    #         duplicated_ids.append(sp['_id'])
    #         if sp['_id'] != mp['_id']:
    #             duplicated[mp['_id']].append(sp['_id'])
    #             new_invalid = InvalidAssets(mongo_id=sp['_id'], parent=mp['_id'], status='duplicate', category='product')
    # print('-' * 50)
    # print('duplicated')
    # pprint(duplicated)

    # get invalid assets from log
    # invalid_assets = get_missing_assets_from_log()
    # with open('uploads/invalid_assets-api-test2-%s.csv' % (datetime.datetime.now().strftime('%Y%m%d%H%M%S')), 'w', newline='') as csvfile:
    #     writer = csv.DictWriter(csvfile, fieldnames=['product_id', 'asset_id', 'status'])
    #     writer.writeheader()
    #     for ia in invalid_assets:
    #         writer.writerow({'product_id': ia.parent, 'asset_id': ia.mongo_id, 'status': ia.status})

    # get duplicated products from log
    # dup_products = get_missing_assets_from_log()
    # with open('uploads/duplicated_products-api-test2-%s.csv' % (datetime.datetime.now().strftime('%Y%m%d%H%M%S')), 'w', newline='') as csvfile:
    #     writer = csv.DictWriter(csvfile, fieldnames=['origin', 'same'])
    #     writer.writeheader()
    #     for ia in dup_products:
    #         if ia.status == 'duplicate':
    #             writer.writerow({'origin': ia.parent, 'same': ia.mongo_id})
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
    elif title == 'livestreams_category':
        start_sync_livestreams_category()
    elif title == 'livestreams_category_delete':
        start_sync_livestreams_category_delete()
    elif title == 'livestreams_experience':
        start_sync_livestreams_experience()
    elif title == 'livestreams_experience_delete':
        start_sync_livestreams_experience_delete()
    elif title == 'orders':
        start_sync_orders()
    elif title == 'orders_delete':
        start_sync_orders_delete()
    elif title == 'payments':
        start_sync_payments()
    elif title == 'payments_delete':
        start_sync_payments_delete()
    elif title == 'shipping':
        start_sync_shipping_classes()
    # elif title == 'shipping_delete':
    # start_sync_shipping_classes_delete()
    return HttpResponse('Hello')


def start_sync_categories():
    print('start syncing categories')
    print('-' * 30)
    print('get products from mongo')
    wapi = woo_api(woocommerce)

    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]
    m_categories = mongo_db['productcategories'].find()
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
    # print('get products from mongo')
    print('read products from file')
    mysql_conn = mysql_db_connect(hk_mysql)
    mysql_cursor = mysql_conn.cursor(dictionary=True, buffered=True)

    with open('uploads/products-shoclef.com-modified-10282020.csv', 'r', encoding='utf-8') as csvfile:
        csv_values = csv.DictReader(csvfile)
        for csv_value in csv_values:
            if 'women_bags' in csv_value['email'] or 'consumer_electronics' in csv_value['email']:
                sync_statues = get_status('products')
                if sync_statues.state == 0:
                    print('-' * 30)
                    print('Break syncing...')
                    break
                print('-' * 50)
                print(csv_value['title'], csv_value['email'])
                print('*' * 50)
                post_from_mysql = mysql_select_table(mysql_cursor, 'wp_posts', where='post_title="%s"' % csv_value['title'].strip(), fetch='one')
                if post_from_mysql:
                    # print('found in woocommerce %s' % post_from_mysql['ID'])
                    user_from_mysql = mysql_select_table(mysql_cursor, 'wp_users', where='user_email="%s"' % csv_value['email'].strip(), fetch='one')
                    if user_from_mysql:
                        # continue
                        print('found in user list %s, updating----' % user_from_mysql['ID'])
                        mysql_update_table(mysql_conn, mysql_cursor, 'wp_posts', {'post_author': user_from_mysql['ID']}, 'ID=%s' % post_from_mysql['ID'])
                    else:
                        print(2, '---', csv_value['title'], csv_value['email'])
                else:
                    print(1, '------', csv_value['title'], csv_value['email'])
    # get currency convert rate
    mysql_db_close(mysql_conn, mysql_cursor)
    save_status('products', 0)


def start_sync_products_temp():
    print('start syncing products')
    print('-' * 30)
    # print('get products from mongo')

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
    # m_products = mongo_db['products'].find().limit(10)
    #
    # for mp in m_products:
    #     sync_statues = get_status('products')
    #     if sync_statues.state == 0:
    #         print('-' * 30)
    #         print('Break syncing...')
    #         break
    #     print('-' * 30)
    #     # pprint(mp)
    #     # check if already exist in log
    #     exist_in_log = get_product_from_log(mongo_id=mp['_id'])
    #     if exist_in_log:
    #         print('product exist in log db', exist_in_log.mongo_id, exist_in_log.woo_id)
    #
    #         if mp['_id'] in fix_products:
    #             print('update product')
    #             exist_in_woo = woo_product_one(wapi, woo_id=exist_in_log.woo_id)
    #             if exist_in_woo:
    #                 update_product(mongo_db, wapi, exist_in_log.woo_id, mp, cc_res)
    #         continue
    #         # check if exist in woocommerce
    #         # exist_in_woo = woo_product_one(wapi, woo_id=exist_in_log.woo_id)
    #         # if exist_in_woo:
    #         #     print('product exist in woocommerce')
    #         #     woo_prod_id = exist_in_woo['id']
    #         #     check all info same with mongo and woocommerce product
    #         # else:
    #         #     woo_prod_id = add_product(mongo_db, wapi, mp, cc_res)
    #     else:
    #         print('product not exist in log db', mp['_id'])
    #         # check if exist in woocommerce
    #         exist_in_woo = woo_product_one(wapi, sku=mp['_id'])
    #         if exist_in_woo:
    #             print('exist in woocommerce')
    #             woo_cat_id = add_category(mapi, wapi, mp['category'])
    #             save_product_to_log(mongo_id=mp['_id'], woo_id=exist_in_woo[0]['id'], category=woo_cat_id)
    #             woo_prod_id = exist_in_woo[0]['id']
    #         else:
    #             print('product not exist in woocommerce')
    #             # insert to woocommerce
    #             woo_prod_id = add_product(mongo_db, wapi, mp, cc_res)
    #     if int(woo_prod_id) > 0:
    #         print('product insert success %s' % woo_prod_id)
    #     else:
    #         print('product insert failed')

    # sync woo to mongo
    # get categories from woocommerce
    page = 1
    per_page = 100
    user_name_candidates = {}
    print('get top categories')
    while True:
        sync_statues = get_status('products')
        if sync_statues.state == 0:
            print('-' * 30)
            print('Break syncing...')
            break
        print('-' * 30)
        # get top category
        top_categories = woo_categories(wapi, page, per_page, 0)
        page += 1
        if top_categories:
            for tc in top_categories:
                sub_page = 1
                print('get sub categories of %s' % tc['name'])
                while True:
                    sub_categories = woo_categories(wapi, sub_page, per_page, tc['id'])
                    sub_page += 1
                    if sub_categories:
                        for sc in sub_categories:
                            user_name_candidates[sc['id']] = slugify(sc['name']).replace('-', '_')
                            sub_sub_page = 1
                            while True:
                                last_categories = woo_categories(wapi, sub_sub_page, per_page, sc['id'])
                                sub_sub_page += 1
                                if last_categories:
                                    for lc in last_categories:
                                        user_name_candidates[lc['id']] = user_name_candidates[sc['id']]
                                else:
                                    break
                    else:
                        break
        else:
            break
    # print(user_name_candidates)
    print('-' * 50)
    # get products from woocommerce
    page = 1
    csv_values = []
    product_ids = []
    products_no_variation = []
    user_name_list = {
        'cameras_camcorders1@shoclef.com':      ['consumer_electronics1@shoclef.com', 'Riviera Electronics'],
        'cameras_camcorders2@shoclef.com':      ['consumer_electronics1@shoclef.com', 'Riviera Electronics'],
        'cameras_camcorders3@shoclef.com':      ['consumer_electronics1@shoclef.com', 'Riviera Electronics'],
        'car_vehicle_electronics1@shoclef.com': ['consumer_electronics1@shoclef.com', 'Riviera Electronics'],
        'car_vehicle_electronics2@shoclef.com': ['consumer_electronics1@shoclef.com', 'Riviera Electronics'],
        'car_vehicle_electronics3@shoclef.com': ['consumer_electronics1@shoclef.com', 'Riviera Electronics'],
        'cell_phones1@shoclef.com':             ['consumer_electronics2@shoclef.com', "Thompson's Goods"],
        'cell_phones2@shoclef.com':             ['consumer_electronics2@shoclef.com', "Thompson's Goods"],
        'cell_phones3@shoclef.com':             ['consumer_electronics2@shoclef.com', "Thompson's Goods"],
        'computers_tablets1@shoclef.com':       ['consumer_electronics3@shoclef.com', 'Electronics Village'],
        'computers_tablets2@shoclef.com':       ['consumer_electronics3@shoclef.com', 'Electronics Village'],
        'computers_tablets3@shoclef.com':       ['consumer_electronics3@shoclef.com', 'Electronics Village'],
        'gadgets1@shoclef.com':                 ['consumer_electronics1@shoclef.com', 'Riviera Electronics'],
        'gadgets2@shoclef.com':                 ['consumer_electronics1@shoclef.com', 'Riviera Electronics'],
        'gadgets3@shoclef.com':                 ['consumer_electronics1@shoclef.com', 'Riviera Electronics'],
        'men_clothing1@shoclef.com':            ['men_clothing1@shoclef.com', 'Forward Designs'],
        'men_clothing2@shoclef.com':            ['men_clothing2@shoclef.com', 'Old Balance'],
        'men_clothing3@shoclef.com':            ['men_clothing3@shoclef.com', 'Kevin Claire'],
        'women_clothing1@shoclef.com':          ['women_clothing1@shoclef.com', 'Peachy Fashion'],
        'women_clothing2@shoclef.com':          ['women_clothing2@shoclef.com', 'Alyssum Fashion'],
        'women_clothing3@shoclef.com':          ['women_clothing3@shoclef.com', 'Hibiscus Designs'],
        'women_handbags_wallets1@shoclef.com':  ['women_bags1@shoclef.com', 'B&Z'],
        'women_handbags_wallets2@shoclef.com':  ['women_bags2@shoclef.com', 'Fashion Diva'],
        'women_handbags_wallets3@shoclef.com':  ['women_bags3@shoclef.com', 'Honeyland Company'],
        'women_shoes1@shoclef.com':             ['women_shoes1@shoclef.com', 'Slowgold Designs'],
        'women_shoes2@shoclef.com':             ['women_shoes2@shoclef.com', 'Silverose Fashion'],
        'women_shoes3@shoclef.com':             ['women_shoes3@shoclef.com', 'MRYA']
    }

    while True:
        sync_statues = get_status('products')
        if sync_statues.state == 0:
            print('-' * 30)
            print('Break syncing...')
            break
        print('-' * 30)
        woo_prods = woo_products(wapi, page, 100)
        page += 1
        if woo_prods:
            for wp in woo_prods:
                sync_statues = get_status('products')
                if sync_statues.state == 0:
                    print('-' * 30)
                    print('Break syncing...')
                    break
                exist_woo = get_product_from_log(woo_id=wp['id'])
                if exist_woo or wp['id'] in product_ids:
                    print('product exist in woo & mongo')
                    continue
                print('process product %s' % wp['id'])
                prod_data = {
                    '_id':                '',
                    'username':           'Designer Creations',
                    'email':              'shoclef.outnet@shoclef.com',
                    'freeDeliveryTo':     'DOMESTIC',
                    'isDeleted':          'FALSE',
                    'title':              wp['name'],
                    'description':        '',
                    'currency':           'USD',
                    'categoryID':         '',
                    'weightValue':        wp['weight'],
                    'weightUnit':         'oz',
                    'shippingBoxWidth':   '0',
                    'shippingBoxHeight':  '0',
                    'shippingBoxLength':  '0',
                    'unit':               'inch',
                    'brand_name':         '',
                    'seller_name':        'management',
                    'price':              wp['sale_price'] if wp['sale_price'] else 0,
                    'oldPrice':           wp['regular_price'] if wp['regular_price'] else 0,
                    'quantity':           wp['stock_quantity'] if wp['stock_quantity'] else 0,
                    'customCarrier':      '',
                    'customCarrierValue': '',
                    'attributeNames':     '',
                    'attributeValues':    '',
                }
                user_email = ''
                if wp['categories']:
                    prod_data['categoryID'] = wp['categories'][0]['slug']
                    if wp['categories'][0]['id'] in user_name_candidates:
                        user_email = user_name_candidates[wp['categories'][0]['id']] + str(random.randint(1, 3)) + '@shoclef.com'
                        if user_email not in user_name_list:
                            user_name_list[user_email] = ['men_clothing1@shoclef.com', 'Forward Designs']
                    else:
                        user_email = 'men_clothing1@shoclef.com'
                if user_email != '':
                    prod_data['username'] = prod_data['brand_name'] = prod_data['seller_name'] = user_name_list[user_email][1]
                    prod_data['email'] = user_name_list[user_email][0]
                tags = []
                if wp['tags']:
                    # prod_data['brand_name'] = wp['tags'][0]['name']
                    for tag in wp['tags']:
                        tags.append(tag['name'])

                if wp['short_description']:
                    prod_data['description'] = bs(wp['short_description'], 'html.parser').get_text().replace('\n', '  ') + '\n[Tags: ' + ','.join(tags) + ']'

                if wp['dimensions']:
                    prod_data['shippingBoxWidth'] = wp['dimensions']['width']
                    prod_data['shippingBoxHeight'] = wp['dimensions']['height']
                    prod_data['shippingBoxLength'] = wp['dimensions']['length']
                prod_variations = []
                prod_attributes = []
                if wp['type'] == 'variable':
                    if wp['variations']:
                        variation_all = woo_variation(wapi, wp['id'], 0)
                        for variation in variation_all:
                            variation_one = {}
                            for var_attr in variation['attributes']:
                                if var_attr['name'] not in prod_attributes:
                                    prod_attributes.append(var_attr['name'])
                                variation_one[var_attr['name']] = var_attr['option']
                            variation_one['price'] = variation['price']
                            variation_one['oldPrice'] = variation['regular_price']

                            if float(prod_data['price']) == 0 or float(prod_data['price']) > float(variation['price']):
                                prod_data['price'] = variation['price']
                            if float(prod_data['oldPrice']) == 0 or float(prod_data['oldPrice']) > float(variation['regular_price']):
                                prod_data['oldPrice'] = variation['regular_price']

                            variation_one['quantity'] = variation['stock_quantity'] if 'stock_quantity' in variation else 0
                            prod_variations.append(variation_one)
                    else:
                        products_no_variation.append({'id': wp['id'], 'name': wp['name'], 'link': wp['permalink']})
                        continue
                    # print(prod_attributes)
                    # pprint(prod_variations)
                    prod_data['attributeNames'] = ';'.join(prod_attributes)
                    prod_data['attributeValues'] = ''
                    for prod_var in prod_variations:
                        for prod_attr in prod_attributes:
                            if prod_attr in prod_var:
                                prod_data['attributeValues'] += '%s|' % prod_var[prod_attr]
                            else:
                                prod_data['attributeValues'] += '0'
                        prod_data['attributeValues'] += '%s|%s|%s;' % (prod_var['price'], prod_var['oldPrice'], prod_var['quantity'])
                    prod_data['attributeValues'] = prod_data['attributeValues'][:-1]
                wp_images = wp['images']
                wpi = 0
                for wp_image in wp_images[:14]:
                    wpi += 1
                    prod_data['assets%d' % wpi] = wp_image['src']
                for empty_image in range(wpi + 1, 15):
                    prod_data['assets%d' % empty_image] = ''
                product_ids.append(wp['id'])
                csv_values.append(prod_data)
        else:
            break
    csv_fields = ['_id', 'username', 'email', 'assets1', 'assets2', 'assets3', 'assets4', 'assets5', 'assets6', 'assets7', 'assets8', 'assets9', 'assets10', 'assets11', 'assets12',
                  'assets13', 'assets14', 'freeDeliveryTo', 'isDeleted', 'title', 'description', 'currency', 'categoryID', 'weightValue', 'weightUnit', 'shippingBoxWidth',
                  'shippingBoxHeight', 'shippingBoxLength', 'unit', 'brand_name', 'seller_name', 'price', 'oldPrice', 'quantity', 'customCarrier', 'customCarrierValue',
                  'attributeNames', 'attributeValues']

    with open('uploads/products-shoclef.com-%s.csv' % (datetime.datetime.now().strftime('%Y%m%d%H%M%S')), 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
        writer.writeheader()
        for csv_value in csv_values:
            writer.writerow(csv_value)
    print(user_name_list)
    if products_no_variation:
        products_without_variations_fields = ['id', 'name', 'link']
        with open('uploads/products-shoclef.com-without-variations-%s.csv' % (datetime.datetime.now().strftime('%Y%m%d%H%M%S')), 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=products_without_variations_fields)
            writer.writeheader()
            for csv_value in products_no_variation:
                writer.writerow(csv_value)
        # delete products have no variations
        delete_products_ids = [d['id'] for d in products_no_variation]
        page = 0
        per_page = 100
        while True:
            delete_products_sub = delete_products_ids[page * per_page: (page + 1) * per_page - 1]
            page += 1
            if delete_products_sub:
                woo_product_delete(wapi, delete_products_sub)
            else:
                break

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

    users = mongo_db['users'].find()
    for user in users:
        print('-' * 30)
        sync_statues = get_status('users')
        if sync_statues.state == 0:
            print('-' * 30)
            print('1 Break syncing...')
            break
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

    mysql_conn = mysql_db_connect(hk_mysql)
    mysql_cursor = mysql_conn.cursor(dictionary=True, buffered=True)

    wp_users = mysql_select_table(mysql_cursor, 'wp_usermeta', where="meta_key='wp_capabilities' AND meta_value LIKE '%wcfm_vendor%'")
    if wp_users:
        for wpu in wp_users:
            delete_user_from_log(woo_id=wpu['user_id'])
            user_delete(mysql_conn, mysql_cursor, wpu['user_id'])

    mysql_db_close(mysql_conn, mysql_cursor)
    save_status('users_delete', 0)


def start_sync_livestreams():
    print('start syncing livestreams')
    print('-' * 30)
    print('get livestreams from mongo')
    wapi = woo_api(woocommerce)

    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]

    mysql_conn = mysql_db_connect(hk_mysql)
    mysql_cursor = mysql_conn.cursor(dictionary=True, buffered=True)

    livestreams = mongo_db['livestreams'].find()
    for livestream in livestreams:
        print('-' * 30)
        sync_statues = get_status('livestreams')
        if sync_statues.state == 0:
            print('-' * 30)
            print('1 Break syncing...')
            break
        print('livestream', livestream['_id'])
        add_livestream(wapi, mongo_db, mysql_conn, mysql_cursor, livestream)

    # sync from woo to mongo
    mysql_conn = mysql_db_connect(hk_mysql)
    mysql_cursor = mysql_conn.cursor(dictionary=True, buffered=True)

    woo_livestreams = woo_livestreams_get(mysql_conn, mysql_cursor)

    mysql_db_close(mysql_conn, mysql_cursor)
    mysql_db_close(mysql_conn, mysql_cursor)
    save_status('livestreams', 0)


def start_sync_livestreams_delete():
    print('start syncing livestreams_delete')
    print('-' * 30)
    wapi = woo_api(woocommerce)

    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]

    mysql_conn = mysql_db_connect(hk_mysql)
    mysql_cursor = mysql_conn.cursor(dictionary=True, buffered=True)
    woo_livestreams = mysql_select_table(mysql_cursor, 'wp_posts', where='post_type="livestream"')
    if woo_livestreams:
        for wl in woo_livestreams:
            delete_livestream_from_db(mysql_conn, mysql_cursor, wl['ID'])

    mysql_db_close(mysql_conn, mysql_cursor)

    save_status('livestreams_delete', 0)


def start_sync_livestreams_category():
    print('start syncing livestream categories')
    print('-' * 30)
    print('get livestream categories from mongo')
    wapi = woo_api(woocommerce)
    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]
    mongo_lcs = mongo_db['livestreamcategories'].find().sort('order', -1)
    mysql_conn = mysql_db_connect(hk_mysql)
    mysql_cursor = mysql_conn.cursor(dictionary=True, buffered=True)

    for mlc in mongo_lcs:
        print(mlc['name'])
        add_livestream_category(wapi, mongo_db, mysql_conn, mysql_cursor, mlc)

    mysql_db_close(mysql_conn, mysql_cursor)
    save_status('livestreams_category', 0)


def start_sync_livestreams_category_delete():
    print('start deleting livestream categories')
    print('-' * 30)
    print('get livestream categories from mongo')
    wapi = woo_api(woocommerce)
    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]
    mongo_lcs = mongo_db['livestreamcategories'].find().sort('order', -1)
    mysql_conn = mysql_db_connect(hk_mysql)
    mysql_cursor = mysql_conn.cursor(dictionary=True, buffered=True)

    for mlc in mongo_lcs:
        exist_cat = get_livestream_category_from_log(mlc['_id'])
        if exist_cat:
            mysql_delete_table(mysql_conn, mysql_cursor, 'wp_terms', 'term_id=%s' % exist_cat.woo_id)
            mysql_delete_table(mysql_conn, mysql_cursor, 'wp_term_taxonomy', 'term_id=%s' % exist_cat.woo_id)
            exist_cat.delete()
    remain_cats = mysql_select_table(mysql_cursor, 'wp_term_taxonomy', where='taxonomy="livestream_category"')
    if remain_cats:
        for rc in remain_cats:
            mysql_delete_table(mysql_conn, mysql_cursor, 'wp_terms', 'term_id=%s' % rc['term_id'])
            mysql_delete_table(mysql_conn, mysql_cursor, 'wp_term_taxonomy', 'term_id=%s' % rc['term_id'])

    mysql_db_close(mysql_conn, mysql_cursor)
    save_status('livestreams_category_delete', 0)


def start_sync_livestreams_experience():
    print('start syncing livestream experiences')
    print('-' * 30)
    print('get livestream experience from mongo')
    wapi = woo_api(woocommerce)
    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]
    mongo_les = mongo_db['livestreamexperiences'].find().sort('order', -1)
    mysql_conn = mysql_db_connect(hk_mysql)
    mysql_cursor = mysql_conn.cursor(dictionary=True, buffered=True)

    for mle in mongo_les:
        print(mle['name'])
        add_livestream_experience(wapi, mongo_db, mysql_conn, mysql_cursor, mle)

    mysql_db_close(mysql_conn, mysql_cursor)
    save_status('livestreams_experience', 0)


def start_sync_livestreams_experience_delete():
    print('start deleting livestream experiences')
    print('-' * 30)
    print('get livestream experiences from mongo')
    wapi = woo_api(woocommerce)
    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]
    mongo_lcs = mongo_db['livestreamexperiences'].find().sort('order', -1)
    mysql_conn = mysql_db_connect(hk_mysql)
    mysql_cursor = mysql_conn.cursor(dictionary=True, buffered=True)

    for mlc in mongo_lcs:
        exist_cat = get_livestream_experience_from_log(mlc['_id'])
        if exist_cat:
            mysql_delete_table(mysql_conn, mysql_cursor, 'wp_terms', 'term_id=%s' % exist_cat.woo_id)
            mysql_delete_table(mysql_conn, mysql_cursor, 'wp_term_taxonomy', 'term_id=%s' % exist_cat.woo_id)
            exist_cat.delete()
    remain_cats = mysql_select_table(mysql_cursor, 'wp_term_taxonomy', where='taxonomy="experience"')
    if remain_cats:
        for rc in remain_cats:
            mysql_delete_table(mysql_conn, mysql_cursor, 'wp_terms', 'term_id=%s' % rc['term_id'])
            mysql_delete_table(mysql_conn, mysql_cursor, 'wp_term_taxonomy', 'term_id=%s' % rc['term_id'])

    mysql_db_close(mysql_conn, mysql_cursor)
    save_status('livestreams_experience_delete', 0)


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


def start_sync_shipping_classes():
    print('start syncing shipping classes')
    print('-' * 30)
    print('get custom carriers from mongo')
    wapi = woo_api(woocommerce)
    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]

    custom_carriers = mongo_db['customcarriers'].find()
    for cc in custom_carriers:
        sync_statues = get_status('shipping')
        if sync_statues.state == 0:
            print('-' * 30)
            print('1 Break syncing...')
            break
        add_shipping_class_to_woo(wapi, mapi, cc)

    save_status('shipping', 0)
