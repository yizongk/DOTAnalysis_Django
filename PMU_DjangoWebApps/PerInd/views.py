from django.shortcuts import render
from django.http import HttpResponse

from django.views.generic import TemplateView
from django.views import generic
from .models import *
# Create your views here.

def get_cur_client(request):
    cur_client = request.META['REMOTE_USER']
    return cur_client

'''
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

def about(request):
    return HttpResponse("This will be the ABOUT page")

def contact(request):
    return HttpResponse("This will be the CONTACT page")

def webgrid(request):
    latest_user_list = Users.objects.order_by('-user_id')[:5]

    context = {
        'latest_user_list': latest_user_list
    }

    return render(request, 'PerInd.template.webgrid.html', context)
'''

def get_user_category_pk_list(username):
    try:
        user_permissions_list = UserPermissions.objects.all()
        user_permissions_list = user_permissions_list.filter(user__login=username)
        return [x.category.category_id for x in user_permissions_list]
    except Exception as e:
        print("Exception: get_user_category_pk_list(): {}".format(e))
        return False

class HomePageView(TemplateView):
    template_name = 'template.home.html'

class AboutPageView(TemplateView):
    template_name = 'template.about.html'
    
class ContactPageView(TemplateView):
    template_name = 'template.contact.html'

class WebGridPageView(generic.ListView):
    template_name = 'PerInd.template.webgrid.html'
    context_object_name = 'indicator_data_entries'

    def get_queryset(self):
        # return Users.objects.order_by('-user_id')[:5]
        # print("This is the user logged in!!!: {}".format(self.request.user))
        indicator_data_entries = IndicatorData.objects.all()

        # Filter for only authorized Categories of Indicator Data
        category_pk_list = get_user_category_pk_list(self.request.user)
        indicator_data_entries = indicator_data_entries.filter(indicator__category__pk__in=category_pk_list)

        # Filter for only Active indicator
        # Filter for only last four year
        # Filter for only searched indicator title

        # Sort it asc or desc on sort_by

        return indicator_data_entries
