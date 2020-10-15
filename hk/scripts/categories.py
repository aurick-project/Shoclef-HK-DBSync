import requests
from hk.woocommerce_connect import *
from hk.model import *


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
                        else:
                            invalid_asset_to_log = InvalidAssets(mongo_id=cat_image_in_mongo['_id'], parent=cat_in_mongo['_id'], category='category')
                            invalid_asset_to_log.save()
                    else:
                        invalid_asset_to_log = InvalidAssets(mongo_id=cat_image_in_mongo['_id'], parent=cat_in_mongo['_id'], category='category')
                        invalid_asset_to_log.save()
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
            except Exception as e:
                print('cat error 1', e)
                print('get category from mongo failed')
    return woo_cat_id


def delete_cat_from_woocommerce(wapi, woo_id):
    print('delete category from woocommerce %s' % woo_id)
    woo_category_delete(wapi, woo_id)
    cat_from_log = get_category_from_log(woo_id=woo_id)
    if cat_from_log:
        print('delete category from log %s' % woo_id)
        cat_from_log.delete()
