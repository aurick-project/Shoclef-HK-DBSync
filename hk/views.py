import json
from pprint import pprint
from django.http import HttpResponse
from django.shortcuts import redirect, render
from hk.mysql_connect import *
from hk.mongo_connect import *
from hk.settings import *
from hk.scripts.products import *
from hk.scripts.categories import *
from hk.scripts.tags import *
from hk.scripts.users import *
from hk.scripts.livestreams import *
from hk.scripts.orders import *
from hk.scripts.payments import *


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


def check_products(request):
    mapi = mongo_connect(mongo['url'])
    mongo_db = mapi[mongo['dbname']]
    m_products = mongo_db['products'].find()
    duplicated = {}
    duplicated_ids = []
    missing_assets = {}
    missing_shipping_box = []
    missing_sellerinfo = []
    missing_customcarrier = []
    missing_customcarrier_value = []
    image_formats = ("image/png", "image/jpeg", "image/jpg")
    prod_cnt = 0
    for mp in m_products:
        prod_cnt += 1
        print(prod_cnt, mp['_id'])
        missing_assets_for_one = []
        mp_assets = mp['assets']
        if mp_assets:
            for mp_asset in mp_assets:
                ma = mongo_db['assets'].find_one({'_id': mp_asset})
                if ma:
                    # response = requests.head(ma['url'])
                    # if response.headers['content-type'] not in image_formats:
                    #     missing_assets_for_one.append({'state': 'uploaded but not available', 'id': mp_asset})
                    continue
                else:
                    missing_assets_for_one.append({'state': 'not exist', 'id': mp_asset})
        if missing_assets_for_one:
            missing_assets[mp['_id']] = missing_assets_for_one
        if mp['_id'] in duplicated_ids:
            continue
        same_prod = mongo_db['products'].find({'title': mp['title'], 'price': mp['price']})
        if same_prod.count() > 1:
            duplicated[mp['_id']] = []
            for sp in same_prod:
                duplicated_ids.append(sp['_id'])
                if sp['_id'] != mp['_id']:
                    duplicated[mp['_id']].append(sp['_id'])
    print('-' * 50)
    print('duplicated')
    pprint(duplicated)

    print('-' * 50)
    print('missing assets')
    pprint(missing_assets)

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
    elif title == 'orders':
        start_sync_orders()
    elif title == 'orders_delete':
        start_sync_orders_delete()
    elif title == 'payments':
        start_sync_payments()
    elif title == 'payments_delete':
        start_sync_payments_delete()
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
    m_products = mongo_db['products'].find()
    fixed = ["9b376793-36ae-45b6-9831-02a7362fe92f", "5b672ab0-7fb6-4a04-8fb2-b8eee17e9b43", "28149e68-e092-4572-9cdf-fdd295c2a6a0", "fa845ec8-bef4-4964-bfee-1b05ee47e0b3",
             "c5c9cbc1-a121-4069-960a-dbd40b34d249", "449d0012-14f6-40a1-a2e6-30ef6f3611c7", "2ddcf011-142d-43a3-b6e9-99ca30cb6b11", "1fe1af0f-be47-4dd0-8cc1-73b2c35e5235",
             "b7371328-c708-4580-8024-97504461e92a", "c76b7cf6-b505-4d95-8e12-ee3592bb1ed0", "721b45b8-9f1a-4a96-9e14-117f1b01cb69", "4fda4d1e-92d7-4a62-9387-1c59a8b7d589",
             "832e6d3d-5aae-459f-865c-776cbc68bfeb", "78fe5543-e268-4a6c-8ea1-8f0aa834ef4b", "3440a1e5-4e54-45c6-8544-cf7e16697358", "28149e68-e092-4572-9cdf-fdd295c2a6a0",
             "f65b52f3-f15f-44e2-9f56-09c14cfe3042", "f01cc95e-0f58-43b6-a7b5-544b9fed14ce", "f20f498c-2096-4516-867d-c51f59b192d8", "50ab156c-e1a8-41a6-b9e6-5bef1f09aaf8",
             "d584aaf1-0fe0-45b4-bb9a-6bf3f5167aa8", "f01cc95e-0f58-43b6-a7b5-544b9fed14ce", "f20f498c-2096-4516-867d-c51f59b192d8", "50ab156c-e1a8-41a6-b9e6-5bef1f09aaf8",
             "af26e2f7-d0c1-466f-91f5-f798244b37cb", "6f67a93b-2d11-46a7-bfd6-832f5db6a3f3", "8fbfc41a-cccf-4c8b-b3a2-a3196267ee80", "7b8a995b-cd86-4578-a397-fea55ac5fa20",
             "a5abffaf-3dfa-49d4-a392-b0e80712fb80", "c88d74af-d040-4151-aff2-d7b64db429df", "e2940234-db43-4c70-b2ac-83109b8f7f6c", "45c4dc71-3c05-428e-acb7-55cc541c72de",
             "91b10d7a-84c9-47e3-a834-86a4d7c2e991", "fa59df64-70b4-4a3c-9fca-748d728adf5c", "846ac6dc-67ed-4e36-b68f-2b5a24cee528", "b88ed9bd-816d-48ed-ba84-c1c9cc92224d",
             "f60dc0cd-43ba-4370-b5d8-4ace3f78a4b3", "d9d731e0-68bf-4b2e-a231-5a6271f7e2f4", "d4849ff3-00cd-40f1-bdfc-ff3b3eb62b61", "ac53ebb6-96c1-4318-83b5-b5c822a978de",
             "238afa3c-d184-4ecc-bc2c-dce6b60634d1", "ee08d8b5-2d72-4eab-8781-171bc442f1c1", "08235b21-222b-4b1d-ab9f-f0798dfa0fa6", "a1954caf-a238-4623-b833-e01e6b6e4259",
             "b271b7f5-2442-4fe2-9c40-d55444dfc467", "0e2f3844-16ec-4092-812a-3d05c0fd458c", "9648614e-2d37-46c1-beb0-5b40dabc5d01", "0fe34f91-1bcd-4193-9c09-082be4520c82",
             "157181bf-2aec-4a76-b66d-5c809400b737", "abc78d70-f6f7-467f-a156-60db5eabcd99", "20727d76-f966-4d36-a811-b8568d163bf4", "821c0dd2-1c47-480e-8151-d12a77cb7c4b",
             "7d0e02cd-9812-41b8-adb4-cf83fed57214", "6f219fd1-24f9-4f1a-8841-78e59976f6b2", "1296459f-f3e3-4144-8d97-82c6f53da38f", "c57dd046-ceff-46a1-bac2-583d763c2025",
             "0f2fcd34-e41a-438e-b2a3-5fdd797f87f3", "9648614e-2d37-46c1-beb0-5b40dabc5d01", "0fe34f91-1bcd-4193-9c09-082be4520c82", "157181bf-2aec-4a76-b66d-5c809400b737",
             "abc78d70-f6f7-467f-a156-60db5eabcd99", "20727d76-f966-4d36-a811-b8568d163bf4", "821c0dd2-1c47-480e-8151-d12a77cb7c4b", "7d0e02cd-9812-41b8-adb4-cf83fed57214",
             "6f219fd1-24f9-4f1a-8841-78e59976f6b2", "1296459f-f3e3-4144-8d97-82c6f53da38f", "c57dd046-ceff-46a1-bac2-583d763c2025", "0f2fcd34-e41a-438e-b2a3-5fdd797f87f3",
             "d9c38e28-2998-4078-88fe-6cd51931dcc0", "da55bf8c-a351-4d9b-b084-02f5f7928c21", "55f894e4-b84e-4fb2-9ed3-915eefcd7f7b", "838d78e9-e91e-4051-9e6a-6d3eb7362212",
             "3849e792-a813-494e-b5c5-507abd80121d", "3d7c72eb-d691-4beb-9fe4-9abb3522e919", "93502ac5-a2a3-4f10-9c3a-16127c81e716", "14f26a1a-7678-432f-ac87-b6d8e0c62b27",
             "fd2c453f-6a2b-41f0-9f7c-bda29b660a51", "f67d4852-54f4-4394-aefc-52cb60438830", "fd596191-41c3-4562-ac20-ad04c8a55d4c", "d7d2f4e1-757c-4f97-8db7-c08744e26c17",
             "f333286f-638a-44db-a2ee-cd5f89442562", "d00a9866-5d25-4966-a4bb-e88eb149f236", "08f441c0-2455-4cd3-becf-4fd285493651", "c79521b5-f12e-4890-87f3-cc8b674a6097",
             "0b0a85bc-95e1-488b-987d-ca36bcafc807", "55fe6c14-7bc0-4921-b4dc-6ddef961cecc", "8de909b0-d6a3-4651-bb6f-749717c75a5f", "c08912a7-80c1-4223-be94-5f00c1d3dc05",
             "b532b29f-f8fd-4058-af14-0e807b358fe5", "e21180cf-3f01-4a6c-be29-d22b182b36f0", "2017aeda-f34d-4775-89f4-86235de3afb3", "b409a371-103e-468f-8c38-8b7151f30a6d",
             "fe31edba-2623-41db-80a6-35bb0af97f7f", "2017aeda-f34d-4775-89f4-86235de3afb3", "b409a371-103e-468f-8c38-8b7151f30a6d", "fe31edba-2623-41db-80a6-35bb0af97f7f",
             "dab12f34-9c7c-42b6-a5fe-7b963feb680b", "ed03f28f-c432-4b3f-8a18-e741556669fd", "860059f4-4de1-4ae1-b024-7ea8eb6b21bf", "dab12f34-9c7c-42b6-a5fe-7b963feb680b",
             "ed03f28f-c432-4b3f-8a18-e741556669fd", "860059f4-4de1-4ae1-b024-7ea8eb6b21bf", "5ea1cf85-6c17-445c-bf91-274e91a335de", "b6305f0b-5cfb-4287-b3d8-02bb1bbac895",
             "c373d58f-adef-4647-ab5f-6c3a4d1fa14e", "86c72fba-53a2-4bbc-8d1f-680b9637df2b", "35fb0b1b-77df-4e80-88e0-69b943227cc6", "5408eea8-3f9a-478c-8ea2-fbaf66d5c1af",
             "47c33bff-a94d-4684-b0b4-6aa9fc159a7e", "cb08e5fa-6fd6-47b5-95dd-ad136bf73789", "e4e7af08-d075-48a1-b502-1508d1c5da42", "6779c908-d061-44a6-8dda-e06c4bc982d8",
             "17a6bf40-cc24-4fec-8f26-b1d2c84df318", "d9c38e28-2998-4078-88fe-6cd51931dcc0", "265959fd-2822-4907-866a-cc6d5d3adbe4", "7017a0f9-36a7-49d7-b35d-343c67f8f72a",
             "20896a53-48fe-4e4b-b322-1f424c99cbac", "d2de599a-00e4-4611-8547-ec47d7207c46", ]
    fix_products = [
        "721b45b8-9f1a-4a96-9e14-117f1b01cb69", "832e6d3d-5aae-459f-865c-776cbc68bfeb", "4fda4d1e-92d7-4a62-9387-1c59a8b7d589"]

    have_to_fix = [
        "2c51457a-3384-44f9-b202-b8dbf6a5cb3e",
        "bc8f4983-77de-4249-9d56-bab33fc70d54",
        "c5220c3d-ce36-480a-8bd5-0e1799ddca2e",
        "d74c0ea6-3940-4c13-a729-e68e6ce38498",
        "8aeca80e-697c-4758-bd3d-233544f6eb4c",
        "89fa9898-21b9-40fb-aba3-2ebdd11132e6",
        "af26e2f7-d0c1-466f-91f5-f798244b37cb",
        "14c3870b-42dd-41c0-88d2-6e4a4d0b90ca",
        "1cedd638-7c3f-4060-a0be-5a116b965038",
        "a900aa55-9f8c-4480-ae6e-a6529fe52655",
        "84b72bef-6ba6-4e7e-a353-68dbf872601f",
        "7d397ea5-17b0-4893-ae37-298c69c67605"
    ]
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

            if mp['_id'] in fix_products:
                exist_in_woo = woo_product_one(wapi, woo_id=exist_in_log.woo_id)
                if exist_in_woo:
                    update_product(mongo_db, wapi, exist_in_log.woo_id, mp, cc_res)
            continue
            # check if exist in woocommerce
            # exist_in_woo = woo_product_one(wapi, woo_id=exist_in_log.woo_id)
            # if exist_in_woo:
            #     print('product exist in woocommerce')
            #     woo_prod_id = exist_in_woo['id']
            #     check all info same with mongo and woocommerce product
            # else:
            #     woo_prod_id = add_product(mongo_db, wapi, mp, cc_res)
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
        if int(woo_prod_id) > 0:
            print('product insert success %s' % woo_prod_id)
        else:
            print('product insert failed')
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
    mysql_db_close(mysql_conn, mysql_cursor)
    save_status('livestreams', 0)


def start_sync_livestreams_delete():
    print('start syncing livestreams_delete')
    print('-' * 30)
    print('get users from mongo')
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
