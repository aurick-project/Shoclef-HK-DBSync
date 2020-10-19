from hk.model import *
from hk.woocommerce_connect import *


def add_shipping_class_too_woo(wapi, mapi, mongo_data):
    exist_cc = get_resourece_from_log(mongo_id=mongo_data['_id'], category='shipping')
    if exist_cc:
        print('already exist')
        return exist_cc.woo_id
    shipping_data = {
        'name': mongo_data['name'],
    }
    woo_data = shipping_add(wapi, shipping_data)
    if woo_data:
        woo_id = woo_data['id']
        save_resource_to_log(mongo_id=mongo_data['_id'], woo_id=woo_id, category='shipping')
