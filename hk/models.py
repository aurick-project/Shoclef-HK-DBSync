from django.db import models


# Create your models here.
class Status(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(default='products', max_length=100)
    state = models.IntegerField(default=1)

    def __str__(self):
        return self.title


class Categories(models.Model):
    id = models.AutoField(primary_key=True)
    parent = models.IntegerField(default=0)
    woo_id = models.CharField(default='', max_length=100)
    mongo_id = models.CharField(default='', max_length=100)

    def __str__(self):
        return 'woo:%s mongo:%s' % (self.woo_id, self.mongo_id)


class Tags(models.Model):
    id = models.AutoField(primary_key=True)
    woo_id = models.CharField(default='', max_length=100)
    mongo_id = models.CharField(default='', max_length=100)

    def __str__(self):
        return 'woo:%s mongo:%s' % (self.woo_id, self.mongo_id)


class Products(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.IntegerField(default=0)
    woo_id = models.CharField(default='', max_length=100)
    mongo_id = models.CharField(default='', max_length=100)

    def __str__(self):
        return 'woo:%s mongo:%s' % (self.woo_id, self.mongo_id)


class WUsers(models.Model):
    id = models.AutoField(primary_key=True)
    woo_id = models.CharField(default='', max_length=100)
    mongo_id = models.CharField(default='', max_length=100)
    user_name = models.CharField(default='', max_length=100)
    email = models.CharField(default='', max_length=100)
    avatar = models.CharField(default='', max_length=100)

    def __str__(self):
        return 'woo:%s mongo:%s' % (self.woo_id, self.mongo_id)


class Assets(models.Model):
    id = models.AutoField(primary_key=True)
    woo_id = models.CharField(default='', max_length=100)
    mongo_id = models.CharField(default='', max_length=100)
    category = models.CharField(default='', max_length=100)  # category, product, etc
    parent_id = models.IntegerField(default=0)  # category_id, product_id, etc_id
    source = models.CharField(default='', max_length=200)

    def __str__(self):
        return 'woo:%s mongo:%s' % (self.woo_id, self.mongo_id)


class Livestream(models.Model):
    id = models.AutoField(primary_key=True)
    woo_id = models.CharField(default='', max_length=100)
    mongo_id = models.CharField(default='', max_length=100)

    def __str__(self):
        return 'woo:%s mongo:%s' % (self.woo_id, self.mongo_id)


class LivestreamCategory(models.Model):
    id = models.AutoField(primary_key=True)
    woo_id = models.CharField(default='', max_length=100)
    mongo_id = models.CharField(default='', max_length=100)

    def __str__(self):
        return 'woo:%s mongo:%s' % (self.woo_id, self.mongo_id)


class LivestreamExperience(models.Model):
    id = models.AutoField(primary_key=True)
    woo_id = models.CharField(default='', max_length=100)
    mongo_id = models.CharField(default='', max_length=100)

    def __str__(self):
        return 'woo:%s mongo:%s' % (self.woo_id, self.mongo_id)


class InvalidAssets(models.Model):
    id = models.AutoField(primary_key=True)
    mongo_id = models.CharField(default='', max_length=100)
    parent = models.CharField(default='', max_length=100)
    category = models.CharField(default='product', max_length=100)

    def __str__(self):
        return 'mongo:%s' % self.mongo_id
