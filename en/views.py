from django.http import HttpResponse
from django.shortcuts import render


# Create your views here.
def index(request):
    print('start en')
    return HttpResponse('AAA')
