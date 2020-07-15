from django.shortcuts import render
from django.http import HttpResponse

from django.views.generic import TemplateView
# Create your views here.

def get_cur_client(request):
    cur_client = request.META['REMOTE_USER']
    return cur_client

def index(request):
    cur_client = get_cur_client(request)
    return HttpResponse("""
    <!DOCTPYE html>
    <html>

    <head>
        <title>Home Page - Performance Indicator Portal</title>
    </head>

    <body>
        <div>
            <ul>
                <li><a href="/PerInd/about">About</a></li>
                <li><a href="/PerInd/contact">Contact</a></li>
                <li><a href="/PerInd/webgrid">WebGrid - Will remove from this list in prod</a></li>
            </ul>
            <p class="nav navbar-text navbar-right">Hello, {}!</p>
        </div>
    </body>

    </html>
    """.format(cur_client))
'''
def about(request):
    return HttpResponse("This will be the ABOUT page")

def contact(request):
    return HttpResponse("This will be the CONTACT page")
'''
def webgrid(request):
    return HttpResponse("This will be WEBGRID PAGE")

class HomePageView(TemplateView):
    template_name = 'home.html'

 
class AboutPageView(TemplateView):
    template_name = 'about.html'
    
class ContactPageView(TemplateView):
    template_name = 'contact.html'
