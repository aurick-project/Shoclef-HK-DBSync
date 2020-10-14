from pprint import pprint
from hk.mysql_connect import *
from hk.settings import *
from hk.model import *
from hk.woocommerce_connect import *


def user_add(mapi, wapi, user):
    # check if user name already exist in log
    print(user['_id'])
    name = user['_id']
    if 'name' in user:
        name = user['name']
    email = user['_id'] + '@tempmail.tmp'
    if 'email' in user:
        email = user['email']
    exist_name_log = get_user_from_log(name=name)
    if exist_name_log:
        name = email.split('@')[0]
        exist_name_log1 = get_user_from_log(name=name)
        if exist_name_log1:
            if 'phone' in user:
                name = user['phone'].replace('+', '').replace(' ', '').replace('(', '').replace(')', '')
            else:
                name = user['email']
    user_data = {
        'url':    woocommerce['url'] + woocommerce['user_url'] + '/register',
        'header': {
            'Cache-Control': 'no-cache',
            'Content-Type':  'application/json'
        },
        'data':   '{"username": "%s", "password": "%s", "email": "%s"}' % (name, email, email)
    }
    user_id = woo_user_insert(user_data)
    if user_id:
        save_user_to_log(user['_id'], user_id, name, email)
        mysql_conn = mysql_db_connect(hk_mysql)
        mysql_cursor = mysql_conn.cursor(dictionary=True, buffered=True)
        wp_usermeta = mysql_update_table(mysql_conn, mysql_cursor, 'wp_usermeta', {'meta_value': 'a:1:{s:11:"wcfm_vendor";b:1;}'},
                                         "user_id=%s and meta_key='wp_capabilities'" % user_id)

        user_name = user['name']
        if '-' in user_name:
            user_name = user_name.split('-')
        else:
            user_name = user_name.split(' ')
        first_name = user['name']
        last_name = user['name']
        try:
            if len(user_name) > 1:
                first_name = user_name[0]
                last_name = user['name'].split(first_name)[-1]
        except:
            pass
        billing_address_1 = ''
        billing_city = ''
        billing_postcode = ''
        billing_country = ''
        billing_state = ''
        billing_phone = ''
        if 'address' in user:
            if 'street' in user['address'] and user['address']['street']:
                billing_address_1 = user['address']['street']
            if 'city' in user['address'] and user['address']['city']:
                billing_city = user['address']['city']
            if 'zipcode' in user['address'] and user['address']['zipcode']:
                billing_postcode = user['address']['zipcode']
            if 'country' in user['address'] and user['address']['country']:
                billing_country = user['address']['country']
            if 'region' in user['address'] and user['address']['region']:
                billing_state = user['address']['region'].split('-')[-1]
        if 'phone' in user and user['phone']:
            billing_phone = user['phone']

        user_avatar = ''
        user_avatar_color = ''
        if 'photo' in user:
            photo_asset = get_image_from_log(mongo_id=user['photo'])
            if photo_asset:
                user_avatar = photo_asset.woo_id
            else:
                # check if assets available
                mongo_asset = mapi['assets'].find_one({'_id': user['photo']})
                if mongo_asset:
                    response = requests.get(mongo_asset['url'])
                    if response.status_code == 200:
                        temp_prod = {
                            'name':   'temp',
                            'images': [{'src': mongo_asset['url'], 'name': mongo_asset['_id']}]
                        }

                        print('insert temp product for user avatar')
                        woo_temp_prod = woo_product_insert(wapi, temp_prod)
                        if woo_temp_prod:
                            woo_temp_id = woo_temp_prod['id']
                            woo_temp_image = woo_temp_prod['images'][0]
                            save_image_to_log(mongo_asset['_id'], woo_temp_image['id'], 'user', source=woo_temp_image['src'])
                            user_avatar = woo_temp_image['id']
                            print('delete temp product for user avatar')
                            woo_product_delete(wapi, [woo_temp_id])

        user_fields = {
            'first_name':           first_name,
            'last_name':            last_name,
            'billing_first_name':   first_name,
            'billing_last_name':    last_name,
            'billing_address_1':    billing_address_1,
            'billing_city':         billing_city,
            'billing_postcode':     billing_postcode,
            'billing_country':      billing_country,
            'billing_state':        billing_state,
            'billing_phone':        billing_phone,
            'shipping_first_name':  first_name,
            'shipping_last_name':   last_name,
            'shipping_address_1':   billing_address_1,
            'shipping_city':        billing_city,
            'shipping_postcode':    billing_postcode,
            'shipping_country':     billing_country,
            'shipping_state':       billing_state,
            'wp_user_avatar':       user_avatar,
            'wp_user_avatar_color': user_avatar_color,
        }
        for meta_key in user_fields.keys():
            print('insert to wp_usermeta %s %s' % (meta_key, user_fields[meta_key]))
            exist_metafield = mysql_select_table(mysql_cursor, 'wp_usermeta', where='user_id=%s and meta_key="%s"' % (user_id, meta_key), fetch='one')
            if exist_metafield:
                mysql_update_table(mysql_conn, mysql_cursor, 'wp_usermeta', {'meta_value': user_fields[meta_key]}, 'umeta_id=%s' % exist_metafield['umeta_id'])
            else:
                mysql_insert_table(mysql_conn, mysql_cursor, 'wp_usermeta', {'user_id': user_id, 'meta_key': meta_key, 'meta_value': user_fields[meta_key]})
        mysql_db_close(mysql_conn, mysql_cursor)


def user_delete(mysql_conn, mysql_cursor, user_id):
    wp_user = mysql_select_table(mysql_cursor, 'wp_users', where='ID=%s' % user_id, fetch='one')
    if wp_user:
        mysql_delete_table(mysql_conn, mysql_cursor, 'wp_users', 'ID=%s' % user_id)
        mysql_delete_table(mysql_conn, mysql_cursor, 'wp_usermeta', 'user_id=%s' % user_id)

