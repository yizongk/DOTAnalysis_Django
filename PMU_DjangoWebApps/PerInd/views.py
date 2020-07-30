from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from django.views.generic import TemplateView
from django.views import generic
from .models import *

from django.views.generic import ListView

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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
        return {
            "success": True,
            "data": [x.category.category_id for x in user_permissions_list],
            "err": '',
            "category_names": [x.category.category_name for x in user_permissions_list],
        }
    except Exception as e:
        print("Exception: get_user_category_pk_list(): {}".format(e))
        return {
            "success": False,
            "data": None,
            "err": "Exception: get_user_category_pk_list(): {}".format(e),
            "category_names": [],
        }

class HomePageView(TemplateView):
    template_name = 'template.home.html'

class AboutPageView(TemplateView):
    template_name = 'template.about.html'
    
class ContactPageView(TemplateView):
    template_name = 'template.contact.html'

# Method Flowchart (the order of execution) for generic.ListView
#     setup()
#     dispatch()
#     http_method_not_allowed()
#     get_template_names()
#     get_queryset()
#     get_context_object_name()
#     get_context_data()
#     get()
#     render_to_response()




class WebGridPageView(generic.ListView):
     model = IndicatorData
     template_name = 'PerInd.template.webgrid.html'
     context_object_name = 'indicator_data_entries'

     paginate_by = 10

     req_success = False
     category_permissions = []
     err_msg = ""
   
   
     def get_queryset(self):
        # return Users.objects.order_by('-user_id')[:5]
        # print("This is the user logged in!!!: {}".format(self.request.user))
        try:
            indicator_data_entries = IndicatorData.objects.all()
           # paginator = Paginator(indicator_data_entries, 3)
           # page = self.request.GET.get('page')
            #posts = paginator.page(page)
           
            
        except Exception as e:
            self.err_msg = "Exception: WebGridPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return IndicatorData.objects.none()

        # Filter for only authorized Categories of Indicator Data, and log the category_permissions
        tmp_result = get_user_category_pk_list(self.request.user)
        self.req_success = tmp_result["success"]
        if tmp_result["success"] == False:
            self.err_msg = "Exception: WebGridPageView(): get_queryset(): {}".format(tmp_result['err'])
            print(self.err_msg)
            return IndicatorData.objects.none()
        category_pk_list = tmp_result["data"]
        self.category_permissions = tmp_result["category_names"]
        indicator_data_entries = indicator_data_entries.filter(indicator__category__pk__in=category_pk_list)

        # Filter for only Active indicator
        # Filter for only last four year
        # Filter for only searched indicator title

        # Sort it asc or desc on sort_by

        return indicator_data_entries

     def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        try:
            context = super().get_context_data(**kwargs)

            # Add my own variables to the context for the front end to shows
            context["req_success"] = self.req_success
            context["err_msg"] = self.err_msg
            context["category_permissions"] = self.category_permissions
            return context
        except Exception as e:
            self.err_msg = "Exception: get_context_data(): {}".format(e)
            context["req_success"] = False
            context["err_msg"] = self.err_msg
            context["category_permissions"] = self.category_permissions
            print(self.err_msg)
            return context
    
    
def SavePerIndDataApi(request):
    id = request.POST.get('id', '')
    table = request.POST.get('table', '')
    column = request.POST.get('column', '')
    value = request.POST.get('value', '')

    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('BEWARE: UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "UNAUTHENTICATE USER!",
        })

    # @TODO Make sure the remote user has permission to the posted record id

    if table == "IndicatorData":
        row = IndicatorData.objects.get(record_id=id)
        print( row.record_id )
        print( row.val )
        print( row.created_date )
        print( row.updated_date )
        print( row.indicator )
        print( row.year_month )
        print( row.update_user )
        print( remote_user )

        # if column=="val":
        #     row.val = value

        # @TODO Update last updated by to current remote user

        # @TODO Update updated date to current time

        # row.save()

        return JsonResponse({
            "post_success": True,
            "post_msg": "",
        })

'''
def page(request):
    entries_list = IndicatorData.objects.all()
    paginator = Paginator(entries_list, 25) # Show 25 contacts per page.
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
	    posts = paginator.page(1)
    except EmptyPage:
	    posts = paginator.page(paginator.num_pages)
    context = {
        "page" : page,
        "posts" : posts
	}
    return render(request, "PerInd.template.webgrid.html", context)
    '''