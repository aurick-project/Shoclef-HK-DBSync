from hk.scripts.categories import *
from hk.scripts.tags import *
from hk.woocommerce_connect import *
from hk.model import *


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


def delete_product_from_woocommerce(wapi, woo_id):
    print('delete product from woocommerce %s' % woo_id)
    woo_product_delete(wapi, woo_id)
    prod_from_log = get_product_from_log(woo_id=woo_id)
    if prod_from_log:
        print('delete product from log %s' % woo_id)
        prod_from_log.delete()