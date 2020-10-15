from .models import *


def get_status(title=''):
    try:
        if title == '':
            states = Status.objects.filter(state=1)
        else:
            states = Status.objects.get(title=title)
        return states
    except:
        pass
    return None


def save_status(title, state):
    try:
        status = Status.objects.get(title=title)
        status.state = state
    except:
        status = Status(title=title, state=state)
    status.save()


def get_product_from_log(woo_id='', mongo_id=''):
    try:
        res = None
        if woo_id != '':
            res = Products.objects.get(woo_id=woo_id)
        if mongo_id != '':
            res = Products.objects.get(mongo_id=mongo_id)
        if woo_id != '' and mongo_id != '':
            res = Products.objects.get(woo_id=woo_id, mongo_id=mongo_id)
        return res
    except:
        pass
    return None


def get_category_from_log(woo_id='', mongo_id=''):
    try:
        res = None
        if woo_id != '':
            res = Categories.objects.get(woo_id=woo_id)
        if mongo_id != '':
            res = Categories.objects.get(mongo_id=mongo_id)
        if woo_id != '' and mongo_id != '':
            res = Categories.objects.get(woo_id=woo_id, mongo_id=mongo_id)
        return res
    except:
        pass
    return None


def get_tag_from_log(woo_id='', mongo_id=''):
    try:
        res = None
        if woo_id != '':
            res = Tags.objects.get(woo_id=woo_id)
        if mongo_id != '':
            res = Tags.objects.get(mongo_id=mongo_id)
        if woo_id != '' and mongo_id != '':
            res = Tags.objects.get(woo_id=woo_id, mongo_id=mongo_id)
        return res
    except:
        pass
    return None


def get_image_from_log(mongo_id='', woo_id='', category='product'):
    try:
        res = None
        if woo_id != '':
            res = Assets.objects.get(woo_id=woo_id, category=category)
        if mongo_id != '':
            res = Assets.objects.get(mongo_id=mongo_id, category=category)
        if woo_id != '' and mongo_id != '':
            res = Assets.objects.get(mongo_id=mongo_id, woo_id=woo_id, category=category)
        return res
    except:
        pass
    return None


def save_image_to_log(mongo_id='', woo_id='', category='product', parent=0, source=''):
    try:
        exist_image = get_image_from_log(mongo_id, woo_id, category)
        if exist_image is None:
            new_image = Assets(mongo_id=mongo_id, woo_id=woo_id, category=category, parent_id=parent, source=source)
            new_image.save()
    except:
        pass


def save_product_to_log(mongo_id='', woo_id='', category=''):
    try:
        exist_product = get_product_from_log(mongo_id=mongo_id)
        if exist_product is None:
            new_product = Products(mongo_id=mongo_id, woo_id=woo_id, category=category)
            new_product.save()
        else:
            exist_product.woo_id = woo_id
            exist_product.category=category
            exist_product.save()
    except:
        pass


def get_user_from_log(mongo_id='', woo_id='', name='', email=''):
    try:
        exist_user = None
        if mongo_id != '':
            exist_user = WUsers.objects.get(mongo_id=mongo_id)
        if woo_id != '':
            exist_user = WUsers.objects.get(woo_id=woo_id)
        if name != '':
            exist_user = WUsers.objects.get(user_name=name)
        if email != '':
            exist_user = WUsers.objects.get(email=email)
        if mongo_id != '' and woo_id != '':
            exist_user = WUsers.objects.get(woo_id=woo_id, mongo_id=mongo_id)
        return exist_user
    except:
        print('get user from log not exist')
    return None


def save_user_to_log(mongo_id, woo_id, name, email):
    new_user = WUsers(mongo_id=mongo_id, woo_id=woo_id, user_name=name, email=email)
    new_user.save()


def delete_user_from_log(mongo_id='', woo_id=''):
    exist_user = None
    if mongo_id != '':
        exist_user = get_user_from_log(mongo_id=mongo_id)
    if woo_id != '':
        exist_user = get_user_from_log(woo_id=woo_id)
    if exist_user:
        exist_user.delete()


def get_livestream_from_log(mongo_id='', woo_id=''):
    try:
        exist_livestream = None
        if mongo_id != '':
            exist_livestream = Livestream.objects.get(mongo_id=mongo_id)
        if woo_id != '':
            exist_livestream = Livestream.objects.get(woo_id=woo_id)
        return exist_livestream
    except:
        print('get livestream from log not exist')
    return None


def save_livestream_to_log(mongo_id='', woo_id=''):
    new_livestream = Livestream(mongo_id=mongo_id, woo_id=woo_id)
    new_livestream.save()
