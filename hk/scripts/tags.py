from hk.model import *
from hk.woocommerce_connect import *


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

    return woo_tag_id
