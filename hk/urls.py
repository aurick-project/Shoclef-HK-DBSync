from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('products/<int:state>', views.products, name='Sync Products'),
]
