import os

from django.http import HttpResponse
from django.shortcuts import redirect, render
from configparser import ConfigParser
from hk.woocommerce_connect import *
from hk.mysql_connect import *
from hk.mongo_connect import *
from hk.settings import *


# Create your views here.
def index(request):

    content = {
        'woo_connect':   False,
        'mongo_connect': False,
        'mysql_connect': False,
        'mysql_log_connect': False
    }
    wapi = woo_api(woocommerce)
    if wapi:
        content['woo_connect'] = True
        prods = wapi.get('products')
        content['prods'] = prods.content.decode('utf-8')

    mapi = mongo_connect(mongo['url'])
    if mapi:
        content['mongo_connect'] = True

    mysql_db = mysql_db_connect(mysql)
    if mysql_db:
        content['mysql_connect'] = True

    return render(request, 'index.html', content)


# Sync products reqeust
def products(request, state):
    if state == 1:
        print('Syncing')
    else:
        print('Stop')
    return redirect(index)


# parse config
def get_config():
    parser = ConfigParser()
    if os.path.isfile('env.ini'):
        try:
            parser.read('env.ini')
            if 'woocommerce' not in parser:
                return None
            w_setting = parser['woocommerce']
            if 'url' not in w_setting or 'api_ck' not in w_setting or 'api_cs' not in w_setting:
                return None

            if 'mongo' not in parser:
                return None
            m_setting = parser['mongo']
            if 'url' not in m_setting or 'dbname' not in m_setting:
                return None
            return parser
        except:
            print('read env.ini failed!')
            return None
    return None
