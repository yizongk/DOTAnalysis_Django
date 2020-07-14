from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def get_cur_client(request):
    cur_client = request.META['REMOTE_USER']
    return cur_client

def index(request):
    cur_client = get_cur_client(request)
    return HttpResponse("Hello {}! You are at the PerInd Index".format(cur_client))