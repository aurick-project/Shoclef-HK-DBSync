# Generated by Django 3.1.2 on 2020-10-11 08:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hk', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assets',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('woo_id', models.CharField(default='', max_length=100)),
                ('mongo_id', models.CharField(default='', max_length=100)),
                ('category', models.CharField(default='', max_length=100)),
                ('parent_id', models.IntegerField(default=0)),
                ('source', models.CharField(default='', max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Categories',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('parent', models.IntegerField(default=0)),
                ('woo_id', models.CharField(default='', max_length=100)),
                ('mongo_id', models.CharField(default='', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Products',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('category', models.IntegerField(default=0)),
                ('woo_id', models.CharField(default='', max_length=100)),
                ('mongo_id', models.CharField(default='', max_length=100)),
            ],
        ),
    ]
