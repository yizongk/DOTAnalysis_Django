from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from django.views.generic import TemplateView
from django.views import generic
from .models import *
from datetime import datetime
from django.utils import timezone
import pytz # For converting datetime objects from one timezone to another timezone
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

# Given a record id, checks if user has permission to edit the record
# @TODO IMPLEMENT THIS LOL
def user_has_permission_to_edit(username, record_id):
    try:
        category_permission_info = get_user_category_pk_list(username)
        if category_permission_info["success"] and len(category_permission_info["data"]) != 0:
            print(category_permission_info["data"])
        else:
            raise ValueError( "Permission denied: '{}' does not have permission to edit {} Category.".format(username,'') )

        return {
            "success": True,
            "data": None,
            "err": '',
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "err": 'Exception: user_has_permission_to_edit(): {}'.format(e),
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
    template_name = 'PerInd.template.webgrid.html'
    context_object_name = 'indicator_data_entries'
    req_success = False
    category_permissions = []
    err_msg = ""

    def get_queryset(self):
        # return Users.objects.order_by('-user_id')[:5]
        # print("This is the user logged in!!!: {}".format(self.request.user))
        try:
            indicator_data_entries = IndicatorData.objects.all()
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
    new_value = request.POST.get('new_value', '')

    # return JsonResponse({
    #     "post_success": False,
    #     "post_msg": "This is a test!",
    # })

    # Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "UNAUTHENTICATE USER!",
        })

    # @TODO Make sure the remote user has permission to the posted record id
    # Authenticate permission for user
    user_perm_chk = user_has_permission_to_edit(remote_user, id)
    if user_perm_chk["success"] == False:
        print("Warning: USER '{}' has no permission to edit record #{}!".format(remote_user, id))
        return JsonResponse({
            "post_success": False,
            "post_msg": "USER '{}' has no permission to edit record #{}!".format(remote_user, id),
        })


    if table == "IndicatorData":
        row = IndicatorData.objects.get(record_id=id)

        if column=="val":
            try:
                row.val = new_value

                # Update [last updated by] to current remote user, also make sure it's active user
                user_obj = Users.objects.get(login=remote_user, active_user=True) # Will throw exception if no user is found with the criteria: "Users matching query does not exist.""
                row.update_user = user_obj

                # Update [updated date] to current time
                # updated_timestamp = datetime.now() # Give 'naive' local time, which happens to be EDT on my home dev machine
                updated_timestamp = timezone.now() # Give 'time zone awared' datetime, but backend is UTC
                row.updated_date = updated_timestamp

                local_updated_timestamp_str_response = updated_timestamp.astimezone(pytz.timezone('America/New_York')).strftime("%B %d, %Y, %I:%M %p")

                row.save()

                return JsonResponse({
                    "post_success": True,
                    "post_msg": "",
                    "value_saved": "",
                    "updated_timestamp": local_updated_timestamp_str_response,
                    "updated_by": remote_user,
                })
            except Exception as e:
                print("Error: SavePerIndDataApi(): Something went wrong while trying to save to the database: {}".format(e))
                return JsonResponse({
                    "post_success": False,
                    "post_msg": "Error: SavePerIndDataApi(): Something went wrong while trying to save to the database: {}".format(e),
                })

    print("Warning: SavePerIndDataApi(): Did not know what to do with the request. The request:\n\nid: '{}'\n table: '{}'\n column: '{}'\n new_value: '{}'\n".format(id, table, column, new_value))
    return JsonResponse({
        "post_success": False,
        "post_msg": "Warning: SavePerIndDataApi(): Did not know what to do with the request. The request:\n\nid: '{}'\n table: '{}'\n column: '{}'\n new_value: '{}'\n".format(id, table, column, new_value),
    })