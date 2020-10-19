from hk.woocommerce_connect import *


def add_shipping_class_to_woo(wapi, mapi, mongo_data):
    exist_cc = get_resourece_from_log(mongo_id=mongo_data['_id'], category='shipping')
    if exist_cc:
        print('already exist')
        return exist_cc.woo_id
    shipping_data = {
        'name': mongo_data['name'],
    }
    woo_data = shipping_add(wapi, shipping_data)
    if woo_data:
        if 'id' in woo_data:
            woo_id = woo_data['id']
            print('add shipping class success %s' % woo_id)
            save_resource_to_log(mongo_id=mongo_data['_id'], woo_id=woo_id, slug=woo_data['slug'], category='shipping')
            return woo_id
        else:
            print(woo_data)
            try:
                return woo_data['data']['resource_id']
            except:
                return None
    return None
