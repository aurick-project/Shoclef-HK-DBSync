import json
import requests
from woocommerce import API
from hk.mysql_connect import *
from hk.model import *


def woo_api(config):
    try:
        wcapi = API(
            url=config['url'],
            consumer_key=config['api_ck'],
            consumer_secret=config['api_cs'],
            version="wc/v3",
            timeout=3000,
            query_string_auth=True,
            wp_api=True
        )
    except:
        return None
    return wcapi


# get products
def woo_products(wcapi, page=1, per_page=100):
    try:
        print('get product page: %s per_page: %s' % (page, per_page))
        products = wcapi.get('products', params={'page': page, 'per_page': per_page})
        # print(products.text)
        if products:
            return products.json()
    except Exception as e:
        print(e)
        print('get product error')
    return None


# get one product
def woo_product_one(wcapi, woo_id='', sku=''):
    try:
        if woo_id != '':
            product = wcapi.get('products/%s' % woo_id)
            if product.status_code == 200:
                return product.json()
            else:
                return None
        elif sku != '':
            product = wcapi.get('products', params={'sku': sku})
            if product.status_code == 200:
                return product.json()
            else:
                return None
    except Exception as e:
        print(e)
    print('get product one error')
    return None


# insert product
def woo_product_insert(wcapi, data):
    try:
        product = wcapi.post('products', data)
        if product.status_code in [200, 201]:
            return product.json()
        elif product.status_code in [400]:
            print(product.json())
            if 'Error getting remote image' in product.json()['message']:
                return product.json()
            else:
                return woo_product_one(wcapi, woo_id=product.json()['resource_id'])
    except Exception as e:
        print('insert product to woocommerce error')
        print(e)
        print(data)
    return None


# update product
def woo_product_update(wcapi, woo_id, data):
    try:
        product = wcapi.put('products/%s' % woo_id, data)
        if product.status_code in [200, 201]:
            return product.json()
        elif product.status_code in [400]:
            print(product.json())
            if 'Error getting remote image' in product.json()['message']:
                return product.json()
            else:
                return woo_product_one(wcapi, woo_id=product.json()['resource_id'])
    except Exception as e:
        print('update product to woocommerce error')
        print(e)
        print(data)
    return None


# delete product
def woo_product_delete(wcapi, prod_id):
    try:
        data = {"delete": prod_id}
        product = wcapi.post('products/batch', data)
        return product.json()
    except:
        print('Delete product from woocmmerce error', prod_id)
    return None


# get categories
def woo_categories(wcapi, page=1, per_page=100, parent=-1):
    try:
        if parent == -1:
            cats = wcapi.get('products/categories', params={'page': page, 'per_page': per_page})
        else:
            cats = wcapi.get('products/categories', params={'page': page, 'per_page': per_page, 'parent': parent})

        return cats.json()
    except:
        print('get %s %s categories from woocommerce failed' % (page, per_page))
    return None


def woo_category_delete(wcapi, cat_id):
    try:
        res = wcapi.delete('products/categories/%s' % cat_id, params={'force': True})
    except:
        print('Category delete error %s' % cat_id)


# insert category
def woo_category_insert(wcapi, cat_data):
    try:
        category = wcapi.post('products/categories', cat_data)
        print(category.json())
        return category
    except:
        print('insert category error')
    return None


# insert category
def woo_tag_insert(wcapi, cat_data):
    try:
        category = wcapi.post('products/tags', cat_data)
        # print(category.json())
        return category
    except:
        print('insert category error')
    return None


# get category
def woo_category(wcapi, woo_id='', slug=''):
    try:
        if woo_id != '':
            category = wcapi.get('products/categories/%s' % woo_id)
            return category.json()
        elif slug != '':
            category = wcapi.get('products/categories', params={'slug': slug})
            return category.json()
    except:
        print('get category error')
    return None


# get category
def woo_tag(wcapi, woo_id='', slug=''):
    try:
        if woo_id != '':
            tag = wcapi.get('products/tags/%s' % woo_id)
            return tag.json()
        elif slug != '':
            tag = wcapi.get('products/tags', params={'slug': slug})
            return tag.json()
    except:
        print('get category error')
    return None


# add user
def woo_user_insert(data):
    try:
        r = requests.request('POST', data['url'], headers=data['header'], data=data['data'])
        print(data['data'], r.content)
        if r.status_code == 200:
            return json.loads(r.content)['id']
    except Exception as e:
        print(e)
    return None


# add shipping class
def shipping_add(wapi, shipping_data):
    try:
        r = wapi.post('products/shipping_classes', shipping_data)
        if r.json():
            return r.json()
    except Exception as e:
        print(e)
    return None


# get variation
def woo_variation(wapi, pid, vid=0):
    try:
        if vid == 0:
            r = wapi.get('products/%s/variations' % pid)
        else:
            r = wapi.get('products/%s/variations/%s' % (pid, vid))
        if r.json():
            return r.json()
    except Exception as e:
        print(e)
    return None
