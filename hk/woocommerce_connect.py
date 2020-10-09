from woocommerce import API


def woo_api(config):
    try:
        wcapi = API(
            url=config['url'],
            consumer_key=config['api_ck'],
            consumer_secret=config['api_cs'],
            version="wc/v3",
            timeout=3000
        )
    except:
        return None
    return wcapi
