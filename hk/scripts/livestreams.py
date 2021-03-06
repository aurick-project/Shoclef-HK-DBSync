import requests
from hk.model import *
from hk.mysql_connect import *
from hk.settings import mongo
from hk.scripts.products import add_product
from hk.woocommerce_connect import *


def add_livestream(wapi, mongo_db, mysql_conn, mysql_cursor, livestream):
    print('-' * 50)
    exist_livestream_in_log = get_livestream_from_log(livestream['_id'])
    if exist_livestream_in_log:
        if livestream['status'] == 'CANCELED':
            print('livestream status changed to CANCELDED, delete livestream')
            delete_livestream_from_db(mysql_conn, mysql_cursor, exist_livestream_in_log.woo_id)
        return None
    else:
        if livestream['status'] == 'CANCELED':
            print("livestream status is CANCELED, skip..")
            return None
        new_livestream = {
            'name':              livestream['title'],
            'type':              'simple',
            'description':       livestream['title'],
            'short_description': livestream['title'],
            'slug':              livestream['_id'],
            'sku':               livestream['_id']
        }

        livestream_assets = []
        exist_assets_log = get_image_from_log(mongo_id=livestream['preview'], category='livestream')
        if exist_assets_log:
            livestream_assets.append({'id': exist_assets_log.woo_id})
        else:
            m_asset = mongo_db['assets'].find_one({'_id': livestream['preview']})
            if m_asset:
                response = requests.head(m_asset['url'])
                image_formats = ("image/png", "image/jpeg", "image/jpg")
                if response.headers['content-type'] in image_formats:
                    livestream_assets.append({'src': m_asset['url'], 'name': m_asset['_id']})
        new_livestream['images'] = livestream_assets

        # add livestream as product
        print('Add livestream as product')
        woo_data = woo_product_insert(wapi, new_livestream)
        print(woo_data)
        if woo_data:
            woo_id = woo_data['id']
            print('product id', woo_id)
            if woo_data['images']:
                for w_image in woo_data['images']:
                    save_image_to_log(w_image['name'], w_image['id'], 'livestream', woo_id, w_image['src'])

            # update post type to livestream
            print("update post type to livestream")
            mysql_update_table(mysql_conn, mysql_cursor, 'wp_posts', {'post_type': 'livestream'}, 'ID=%s' % woo_id)

            # get product list of livestream from mongo
            livestream_product_list = []
            if 'products' in livestream and livestream['products']:
                for lp in livestream['products']:
                    print('get product from log', lp)
                    exist_product_in_log = get_product_from_log(mongo_id=lp)
                    if exist_product_in_log:
                        livestream_product_list.append('%s' % exist_product_in_log.woo_id)
                    else:
                        cc_res = []
                        try:
                            cc_req_res = requests.get('http://www.floatrates.com/daily/usd.json')
                            cc_res = json.loads(cc_req_res.content)
                        except:
                            print('get currency convert rate failed')
                            pass
                        mp = mongo_db['products'].find_one({'_id': lp})
                        if mp:
                            woo_prod_id = add_product(mongo_db, wapi, mp, cc_res)
                            if int(woo_prod_id) > 0:
                                livestream_product_list.append('%s' % woo_prod_id)

            # update product list of livestream
            print("update product list of livestream")
            livestream_prodlist_db = mysql_select_table(mysql_cursor, 'wp_postmeta', where='post_id=%s and meta_key="productlist"' % woo_id, fetch='one')
            if livestream_prodlist_db:
                mysql_update_table(mysql_conn, mysql_cursor, 'wp_postmeta', {'meta_value': ','.join(livestream_product_list)}, 'post_id=%s and meta_key="productlist"' % woo_id)
            else:
                mysql_insert_table(mysql_conn, mysql_cursor, 'wp_postmeta', {'meta_key': 'productlist', 'post_id': woo_id, 'meta_value': ','.join(livestream_product_list)})

            # update stream sources of livestream
            print("update stream sources of livestream")
            if 'channel' in livestream and livestream['channel']:
                livestream_stream_channel = mongo_db['streamchannels'].find_one({'_id': livestream['channel']})
                if livestream_stream_channel:
                    if 'record' in livestream_stream_channel and 'sources' in livestream_stream_channel['record'] and livestream_stream_channel['record']['sources']:
                        for stream in livestream_stream_channel['record']['sources']:
                            stream_source = mongo_db['streamsources'].find_one({'_id': stream})
                            if stream_source:
                                livestream_streamsource_list = mysql_select_table(mysql_cursor, 'wp_postmeta',
                                                                                  where='post_id=%s and meta_key="livestreamsource" and meta_value="%s"' % (
                                                                                      woo_id, stream_source['source'].replace('http://18.185.121.9:5000',
                                                                                                                              'https://apprecording.shoclef.com')))
                                if livestream_streamsource_list:
                                    continue
                                mysql_insert_table(mysql_conn, mysql_cursor, 'wp_postmeta',
                                                   {'post_id':    woo_id, 'meta_key': "livestreamsource",
                                                    'meta_value': stream_source['source'].replace('http://18.185.121.9:5000', 'https://apprecording.shoclef.com')})

            # update stream status of livestream
            print("update stream status of livestream")
            livestream_status = mysql_select_table(mysql_cursor, 'wp_postmeta', where='post_id=%s and meta_key="livestreamstatus"' % woo_id, fetch='one')
            if livestream_status:
                mysql_update_table(mysql_conn, mysql_cursor, 'wp_postmeta', {'meta_value': livestream['status'].lower()}, 'post_id=%s and meta_key="livestreamstatus"' % woo_id)
            mysql_insert_table(mysql_conn, mysql_cursor, 'wp_postmeta',
                               {'post_id': woo_id, 'meta_key': "livestreamstatus", 'meta_value': livestream['status'].lower()})

            # update livestream user
            print("update livestream user")
            livestream_user = get_user_from_log(mongo_id=livestream['streamer'])
            if livestream_user:
                mysql_update_table(mysql_conn, mysql_cursor, 'wp_posts', {'post_author': livestream_user.woo_id}, 'ID=%s' % woo_id)

            # update livestream experience and category
            print('update livestream experience and category')
            if 'categories' in livestream:
                for lc in livestream['categories']:
                    exist_cat = get_livestream_category_from_log(lc)
                    cat_id = None
                    if exist_cat:
                        print('category added in livestream categories')
                        cat_id = exist_cat.woo_id
                    else:
                        print('category not added in livestream categories')
                        livestream_category = mongo_db['livestreamcategories'].find_one({'_id': lc})
                        if livestream_category:
                            print('category found from livestream categories in mongo')
                            new_cat_id = add_livestream_category(wapi, mongo_db, mysql_conn, mysql_cursor, livestream_category)
                            if new_cat_id:
                                print('category added to livestream categories in woo')
                                cat_id = new_cat_id
                            else:
                                print('category not added to livestream categories in woo', new_cat_id)
                        else:
                            print('category not exist in mongo', lc)
                    if cat_id:
                        mysql_insert_table(mysql_conn, mysql_cursor, 'wp_term_relationships', {'object_id': woo_id, 'term_taxonomy_id': cat_id, 'term_order': 0})
            print('save livestream to log')

            # update livestream experience and category
            print('update livestream experience and category')
            if 'experience' in livestream:
                lc = livestream['experience']
                exist_cat = get_livestream_category_from_log(lc)
                cat_id = None
                if exist_cat:
                    print('category added in livestream experience')
                    cat_id = exist_cat.woo_id
                else:
                    print('category not added in livestream experience')
                    livestream_experience = mongo_db['livestreamexperiences'].find_one({'id': lc})
                    if livestream_experience:
                        print('category found from livestream experience in mongo')
                        new_cat_id = add_livestream_experience(wapi, mongo_db, mysql_conn, mysql_cursor, livestream_experience)
                        if new_cat_id:
                            print('category added to livestream experience in woo')
                            cat_id = new_cat_id
                        else:
                            print('category not added to livestream experience in woo', new_cat_id)
                    else:
                        print('category not exist in mongo', lc)
                if cat_id:
                    mysql_insert_table(mysql_conn, mysql_cursor, 'wp_term_relationships', {'object_id': woo_id, 'term_taxonomy_id': cat_id, 'term_order': 0})
            print('save livestream to log')
            save_livestream_to_log(mongo_id=livestream['_id'], woo_id=woo_id)
            return woo_id
    return None


# delete livestream
def delete_livestream_from_db(mysql_conn, mysql_cursor, woo_id):
    try:
        mysql_delete_table(mysql_conn, mysql_cursor, 'wp_posts', 'ID=%s' % woo_id)
        mysql_delete_table(mysql_conn, mysql_cursor, 'wp_postmeta', 'post_id=%s' % woo_id)
        exist_livestream_in_log = get_livestream_from_log(woo_id=woo_id)
        if exist_livestream_in_log:
            exist_livestream_in_log.delete()
    except:
        print('Delete livestream from woocommerce failed', woo_id)


# add livestream category
def add_livestream_category(wapi, mapi, mysql_conn, mysql_cursor, mongo_cat):
    exist_cat = get_livestream_category_from_log(mongo_id=mongo_cat['_id'])
    if exist_cat:
        return exist_cat.woo_id

    cat_data = {
        'name': mongo_cat['name'],
        'slug': mongo_cat['_id']
    }
    cat_assets = None
    if 'imagePath' in mongo_cat:
        try:
            response = requests.head(mongo['cdn_url'] + mongo_cat['imagePath'])
            image_formats = ("image/png", "image/jpeg", "image/jpg")
            if response.headers['content-type'] in image_formats:
                cat_assets = {'src': mongo['cdn_url'] + mongo_cat['imagePath']}

        except:
            pass
    if cat_assets:
        cat_data['image'] = cat_assets
    cat_data = woo_category_insert(wapi, cat_data)
    if cat_data and 'id' in cat_data.json():
        print(cat_data.json()['id'])
        mysql_update_table(mysql_conn, mysql_cursor, 'wp_term_taxonomy', {'taxonomy': 'livestream_category'}, 'term_id=%s' % cat_data.json()['id'])
        save_livestream_category_to_log(mongo_cat['_id'], cat_data.json()['id'])
        return cat_data.json()['id']
    return None


# add livestream category
def add_livestream_experience(wapi, mapi, mysql_conn, mysql_cursor, mongo_cat):
    exist_cat = get_livestream_experience_from_log(mongo_id=mongo_cat['_id'])
    if exist_cat:
        return exist_cat.woo_id

    exp_data = {
        'name':        mongo_cat['name'],
        'slug':        mongo_cat['id'],
        'description': mongo_cat['description']
    }
    cat_assets = None
    if 'imagePath' in mongo_cat:
        try:
            response = requests.head(mongo_cat['imagePath'].replace('${cdn.appAssets}', mongo['cdn_url']))
            image_formats = ("image/png", "image/jpeg", "image/jpg")
            if response.headers['content-type'] in image_formats:
                cat_assets = {'src': mongo_cat['imagePath'].replace('${cdn.appAssets}', mongo['cdn_url'])}

        except:
            pass
    if cat_assets:
        exp_data['image'] = cat_assets
    cat_data = woo_tag_insert(wapi, exp_data)
    if cat_data and 'id' in cat_data.json():
        print(cat_data.json()['id'])
        mysql_update_table(mysql_conn, mysql_cursor, 'wp_term_taxonomy', {'taxonomy': 'experience'}, 'term_id=%s' % cat_data.json()['id'])
        save_livestream_experience_to_log(mongo_cat['_id'], cat_data.json()['id'])
        return cat_data.json()['id']
    return None


def woo_livestreams_get(mysql_conn, mysql_cursor):
    livestreams = mysql_select_table(mysql_cursor, 'wp_posts', where='post_type="livestream" and post_status="publish"')
    livestream_data = []
    for livestream in livestreams:
        exist_livestream_log = get_livestream_from_log(woo_id=livestream['ID'])
        if exist_livestream_log:
            print('Livesteram exist in mongo and woo %s' % livestream['post_title'])
            continue

        livestream_data_one = {'id': livestream['ID'], 'title': livestream['post_title']}
        livestream_metas = mysql_select_table(mysql_cursor, 'wp_postmeta', where='post_id=%s' % livestream['ID'])
        livestream_data_products = []
        for livestream_meta in livestream_metas:
            if livestream_meta['meta_key'] == 'productlist':
                livestream_products = livestream_meta['meta_value'].split(',')
                for livestream_product in livestream_products:

                    # check if product already registered
                    exist_livestream_product_log = get_product_from_log(woo_id=livestream_product)
                    if exist_livestream_product_log:
                        livestream_data_products.append(exist_livestream_product_log.mongo_id)
                    else:
                        print('product not registered on log [woo_id=%s]' % livestream)

