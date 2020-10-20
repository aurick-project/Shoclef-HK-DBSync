from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('check_products/<int:stop>', views.check_products, name='Check Products'),
    path('get_status/<str:title>', views.start_sync, name='Get Status'),
    path('set_status/<str:title>/<int:state>', views.set_status, name='Set Status'),
]
