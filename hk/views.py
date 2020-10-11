import os
import time
import requests
import json

from pprint import pprint

from django.http import HttpResponse
from django.shortcuts import redirect, render
from hk.woocommerce_connect import *
from hk.mysql_connect import *
from hk.mongo_connect import *
from hk.settings import *
from hk.model import *


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
    return HttpResponse('Hello')


def add_category(mapi, wapi, mongo_id):
    woo_cat_id = 0
    parent_woo_id = 0
    exist_in_cat_log = get_category_from_log(mongo_id=mongo_id)
    print('-' * 30)
    print('category %s' % mongo_id)
    if exist_in_cat_log:
        print('category exist in log', exist_in_cat_log.woo_id)
        woo_cat_id = exist_in_cat_log.woo_id
        exist_in_cat_woo = woo_category(wapi, slug=mongo_id)
        if exist_in_cat_woo:
            print('category exist in woocommerce', exist_in_cat_woo[0]['id'])
        else:
            cat_in_mongo = mapi['productcategories'].find_one({'_id': mongo_id})
            cat_data = {
                'name': cat_in_mongo['name'],
                'slug': cat_in_mongo['_id']
            }
            if cat_in_mongo['parent']:
                parent_woo_id = add_category(mapi, wapi, cat_in_mongo['parent'])
                cat_data['parent'] = parent_woo_id

            if cat_in_mongo['image']:
                # check if image exist in log
                cat_image_in_log = get_image_from_log(cat_in_mongo['image'], 'category')
                if cat_image_in_log:
                    cat_data['image'] = [{
                        'id': cat_image_in_log.woo_id
                    }]
                else:
                    cat_image_in_mongo = mapi['assets'].find_one({'_id': cat_in_mongo['image']})
                    if cat_image_in_mongo:
                        response = requests.get(cat_image_in_mongo['url'])
                        if response.status_code == 200:
                            cat_data['image'] = [{
                                'src':  cat_image_in_mongo['url'],
                                'name': cat_image_in_mongo['_id']
                            }]

            woo_cat_data = woo_category_insert(wapi, cat_data)
            if woo_cat_data and woo_cat_data.status_code == 201:
                woo_cat_id = woo_cat_data.json()['id']
                woo_cat_image = woo_cat_data.json()['image']
                if woo_cat_image:
                    save_image_to_log(woo_cat_image['name'], woo_cat_image['id'], 'category', woo_cat_id, woo_cat_image['src'])
                exist_in_cat_log.woo_id = woo_cat_id
                exist_in_cat_log.parent = parent_woo_id
                exist_in_cat_log.save()
            else:
                print('insert category failed! ')
                pprint(cat_data)
    else:
        # check category exist in woocommerce
        exist_in_cat_woo = woo_category(wapi, slug=mongo_id)
        if exist_in_cat_woo:
            print('exist in woocommerce')
            new_category_in_log = Categories(mongo_id=mongo_id, woo_id=exist_in_cat_woo[0]['id'], parent=exist_in_cat_woo[0]['parent'])
            new_category_in_log.save()
            woo_cat_id = exist_in_cat_woo[0]['id']
        else:
            try:
                cat_in_mongo = mapi['productcategories'].find_one({'_id': mongo_id})
                cat_data = {
                    'name': cat_in_mongo['name'],
                    'slug': cat_in_mongo['_id']
                }
                if cat_in_mongo['parent']:
                    parent_woo_id = add_category(mapi, wapi, cat_in_mongo['parent'])
                    cat_data['parent'] = parent_woo_id

                if cat_in_mongo['image']:
                    # check if image exist in log
                    cat_image_in_log = get_image_from_log(cat_in_mongo['image'], 'category')
                    if cat_image_in_log:
                        cat_data['image'] = [{
                            'id': cat_image_in_log.woo_id
                        }]
                    else:
                        cat_image_in_mongo = mapi['assets'].find_one({'_id': cat_in_mongo['image']})
                        if cat_image_in_mongo:
                            response = requests.get(cat_image_in_mongo['url'])
                            if response.status_code == 200:
                                cat_data['image'] = [{
                                    'src':  cat_image_in_mongo['url'],
                                    'name': cat_image_in_mongo['_id']
                                }]

                woo_cat_data = woo_category_insert(wapi, cat_data)
                if woo_cat_data and woo_cat_data.status_code == 201:
                    woo_cat_id = woo_cat_data.json()['id']
                    woo_cat_image = woo_cat_data.json()['image']
                    if woo_cat_image:
                        save_image_to_log(woo_cat_image['name'], woo_cat_image['id'], 'category', woo_cat_id, woo_cat_image['src'])
                    new_category_in_log = Categories(mongo_id=mongo_id, woo_id=woo_cat_id, parent=parent_woo_id)
                    new_category_in_log.save()
                else:
                    print('insert category failed! ')
                    pprint(cat_data)
            except Exception as e:
                print('cat error 1', e)
                print('get category from mongo failed')
    return woo_cat_id


def add_tag(mapi, wapi, mongo_id):
    woo_tag_id = 0
    print('-' * 30)
    exist_tag_in_log = get_tag_from_log(mongo_id=mongo_id)
    if exist_tag_in_log:
        print('tag exist in log %s' % exist_tag_in_log.woo_id)
        woo_tag_id = exist_tag_in_log.woo_id
        exist_in_tag_woo = woo_tag(wapi, slug=mongo_id)
        if exist_in_tag_woo:
            print('tag exist in woocommerce %s' % exist_in_tag_woo[0]['id'])
        else:
            tag_in_mongo = mapi['brands'].find_one({'_id': mongo_id})
            tag_data = {
                'name': tag_in_mongo['name'],
                'slug': tag_in_mongo['_id']
            }
            woo_tag_data = woo_tag_insert(wapi, tag_data)
            if woo_tag_data and woo_tag_data.status_code == 201:
                woo_tag_id = woo_tag_data.json()['id']
                exist_tag_in_log.woo_id = woo_tag_id
                exist_tag_in_log.save()
            else:
                print('insert tag failed! ')
                pprint(tag_data)
    else:
        exist_in_tag_woo = woo_tag(wapi, slug=mongo_id)
        if exist_in_tag_woo:
            print('tag exist in woocommerce %s' % exist_in_tag_woo[0]['id'])
            new_tag_in_log = Categories(mongo_id=mongo_id, woo_id=exist_in_tag_woo[0]['id'])
            new_tag_in_log.save()
            woo_tag_id = exist_in_tag_woo[0]['id']
        else:
            tag_in_mongo = mapi['brands'].find_one({'_id': mongo_id})
            tag_data = {
                'name': tag_in_mongo['name'],
                'slug': tag_in_mongo['_id']
            }
            woo_tag_data = woo_tag_insert(wapi, tag_data)
            if woo_tag_data and woo_tag_data.status_code == 201:
                woo_tag_id = woo_tag_data.json()['id']
                new_tag_in_log = Tags(mongo_id=mongo_id, woo_id=woo_tag_id)
                new_tag_in_log.save()
            else:
                print('insert tag failed! ')
                pprint(tag_data)

    return woo_tag_id


def add_product(mapi, wapi, mongo_product, cc_rate):
    oldPrice = 0
    price = 0
    rate = 1
    if mongo_product['currency'] != 'USD' and mongo_product['currency'].lower() in cc_rate:
        rate = cc_rate[mongo_product['currency'].lower()]['rate']
    if mongo_product['oldPrice'] not in ['', None]:
        oldPrice = float(mongo_product['oldPrice']) / 100
        oldPrice = oldPrice / rate
    if mongo_product['price'] not in ['', None]:
        price = float(mongo_product['price']) / 100
        price = price / rate
    if oldPrice == 0 or price == 0:
        oldPrice = price = max(oldPrice, price)

    product_data = {
        'name':              mongo_product['title'],
        'type':              'simple',
        'regular_price':     "%s" % round(oldPrice, 2),
        'sale_price':        "%s" % round(price, 2),
        'description':       mongo_product['description'],
        'short_description': mongo_product['description'],
        'slug':              mongo_product['_id'],
        'sku':               mongo_product['_id'],
    }

    woo_cat_id = add_category(mapi, wapi, mongo_product['category'])

    if int(woo_cat_id) > 0:
        product_data['categories'] = [{'id': woo_cat_id}]

    woo_tag_id = add_tag(mapi, wapi, mongo_product['brand'])

    if int(woo_tag_id) > 0:
        product_data['tags'] = [{'id': woo_tag_id}]

    mp_assets = []
    if mongo_product['assets']:
        for mp_image in mongo_product['assets']:
            p_image_from_log = get_image_from_log(mongo_id=mp_image, category='product')
            if p_image_from_log:
                mp_assets.append({'id': p_image_from_log.woo_id})
            else:
                mongo_asset = mapi['assets'].find_one({'_id': mp_image})
                # check if image exist on url
                if mongo_asset:
                    response = requests.get(mongo_asset['url'])
                    if response.status_code == 200:
                        mp_assets.append({
                            'src':  mongo_asset['url'],
                            'name': mongo_asset['_id']
                        })
    if mp_assets:
        product_data['images'] = mp_assets
    woo_id = 0
    woo_ins_data = woo_product_insert(wapi, product_data)
    if woo_ins_data:
        woo_id = woo_ins_data['id']
        save_product_to_log(mongo_product['_id'], woo_id, woo_cat_id)
        new_product = Products(woo_id=woo_id, mongo_id=mongo_product['_id'], category=woo_cat_id)
        new_product.save()
        if woo_ins_data['images']:
            for w_image in woo_ins_data['images']:
                save_image_to_log(w_image['name'], w_image['id'], 'product', woo_id, w_image['src'])
    return woo_id


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


def delete_cat_from_woocommerce(wapi, woo_id):
    print('delete category from woocommerce %s' % woo_id)
    woo_category_delete(wapi, woo_id)
    cat_from_log = get_category_from_log(woo_id=woo_id)
    if cat_from_log:
        print('delete category from log %s' % woo_id)
        cat_from_log.delete()


def delete_product_from_woocommerce(wapi, woo_id):
    print('delete product from woocommerce %s' % woo_id)
    woo_product_delete(wapi, woo_id)
    prod_from_log = get_product_from_log(woo_id=woo_id)
    if prod_from_log:
        print('delete product from log %s' % woo_id)
        prod_from_log.delete()
