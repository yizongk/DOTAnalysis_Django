from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import generic

from .models import *
from django.http import JsonResponse
import json


## Return a list of Operations that the client has access to. Returns not limited to 1 Operation, can be multiple.
def get_user_operation_permission(username):
    try:
        operation_permission_query = TblUserList.objects.using('DailyPothole').filter(
            username__exact=username
        ).order_by('operation_id')

        if operation_permission_query.count() > 0:
            return {
                "success": True,
                "err": "",
                "operation_permission_list": [each.operation_id for each in operation_permission_query],
            }
        return {
            "success": False,
            "err": "Cannot find any allowed unit_number for '{}'".format(username),
        }
    except Exception as e:
        print("Exception: DailyPothole: get_user_operation_permission(): {}".format(e))
        return {
            "success": False,
            "err": 'Exception: DailyPothole: get_user_operation_permission(): {}'.format(e),
        }


## Check if remote user is admin and is active
def user_is_active_admin(username):
    try:
        admin_query = TblUserList.objects.using('DailyPothole').filter(
            username=username,
            is_admin=True, ## Filters for Admins
        )
        if admin_query.count() > 0:
            return {
                "isAdmin": True,
                "err": "",
            }
        return {
            "isAdmin": False,
            "err": '{} is not an active Admin'.format(username),
        }
    except Exception as e:
        print("Exception: user_is_active_admin(): {}".format(e))
        return {
            "isAdmin": None,
            "err": 'Exception: user_is_active_admin(): {}'.format(e),
        }


# Create your views here.
class HomePageView(TemplateView):
    template_name = 'DailyPothole.template.home.html'
    client_is_admin = False

    def get_context_data(self, **kwargs):
        try:
            ## Call the base implementation first to get a context
            context = super().get_context_data(**kwargs)
            self.client_is_admin = user_is_active_admin(self.request.user)["isAdmin"]
            context["client_is_admin"] = self.client_is_admin
            return context
        except Exception as e:
            context["client_is_admin"] = False
            return context


class AboutPageView(TemplateView):
    template_name = 'DailyPothole.template.about.html'


class ContactPageView(TemplateView):
    template_name = 'DailyPothole.template.contact.html'


class DataCollectionPageView(generic.ListView):
    template_name = 'DailyPothole.template.datacollection.html'
    context_object_name = 'not_used'

    req_success = False
    err_msg = ""

    client_is_admin = False
    operation_list = []
    boro_list = []
    today = None

    def get_queryset(self):
        # Check for Active Admins
        self.client_is_admin = user_is_active_admin(self.request.user)["isAdmin"]

        ## Get the core data
        try:
            if self.client_is_admin:
                self.operation_list = [each.operation for each in TblOperation.objects.using('DailyPothole').all()]
                self.boro_list = [each.boro_long for each in TblBoros.objects.using('DailyPothole').all()]
            else:
                ## Get the remote user's Operation list and Borough list
                user_objs = TblUserList.objects.using('DailyPothole').filter(
                    username__exact=self.request.user
                ).order_by('operation_id')

                self.operation_list = [each.operation_id.operation for each in user_objs]
                self.boro_list = [each.boros_id.boro_long for each in user_objs]

        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: DateCollectionPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return TblPotholeMaster.objects.none()

        self.req_success = True
        return TblPotholeMaster.objects.none()

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)

            context["req_success"] = self.req_success
            context["err_msg"] = self.err_msg

            context["client_is_admin"] = self.client_is_admin
            context["operation_list"] = self.operation_list
            context["boro_list"] = self.boro_list
            from django.utils import timezone as tz, dateformat
            context["today"] = dateformat.format(tz.localtime(tz.now()).date(), 'Y-m-d')
            return context
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: get_context_data(): {}".format(e)
            print(self.err_msg)

            context = super().get_context_data(**kwargs)
            context["req_success"] = self.req_success
            context["err_msg"] = self.err_msg

            context["client_is_admin"] = False
            context["operation_list"] = []
            context["boro_list"] = []
            context["today"] = None
            return context


class DataGridPageView(generic.ListView):
    template_name = 'DailyPothole.template.datagrid.html'
    context_object_name = 'daily_pothole'

    req_success = False
    err_msg = ""

    client_is_admin = False

    def get_queryset(self):
        # Check for Active Admins
        self.client_is_admin = user_is_active_admin(self.request.user)["isAdmin"]

        ## Get the core data
        try:
            if self.client_is_admin:
                pothole_data = TblPotholeMaster.objects.using('DailyPothole').all().order_by('repair_date', 'boros_id', 'operation_id')
            else:
                # operation_for_user_list = get_user_operation_permission(self.request.user)
                # if operation_for_user_list['success'] == False:
                #     raise ValueError('get_user_operation_permission() failed: {}'.format(operation_for_user_list['err']))
                # else:
                #     allowed_operation_list = operation_for_user_list['operation_permission_list']

                # pothole_data = TblPotholeMaster.objects.using('DailyPothole').filter(
                #     operation_id__in=allowed_operation_list,
                # ).order_by('repair_date', 'boros_id', 'operation_id')
                raise ValueError("'{}' is not an Admin, and is not authorized to see this page.".format(self.request.user))

        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: DateViewPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return TblPotholeMaster.objects.none()

        self.req_success = True
        return pothole_data

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)

            context["req_success"] = self.req_success
            context["err_msg"] = self.err_msg

            context["client_is_admin"] = self.client_is_admin
            return context
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: get_context_data(): {}".format(e)
            print(self.err_msg)

            context = super().get_context_data(**kwargs)
            context["req_success"] = self.req_success
            context["err_msg"] = self.err_msg

            context["client_is_admin"] = False
            return context


## Create User Mgmt view
## Create Backend script to generate the database date
## Create Update API
## Default the Today's date in the data entry
## Redesign the data line separation
def UpdatePotholesData(request):

    if request.method != "POST":
        return JsonResponse({
            "post_success": True,
            "post_msg": "{} HTTP request not supported".format(request.method),
        })


    # ## Authenticate User
    # remote_user = None
    # if request.user.is_authenticated:
    #     remote_user = request.user.username
    # else:
    #     print('Warning: UserPermissionsPanelApiUpdateData(): UNAUTHENTICATE USER!')
    #     return JsonResponse({
    #         "post_success": False,
    #         "post_msg": "UserPermissionsPanelApiUpdateData():\n\nUNAUTHENTICATE USER!",
    #         "post_data": None,
    #     })


    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "DailyPothole: UpdatePotholesData():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    try:
        # id = json_blob['id']
        # table = json_blob['table']
        # column = json_blob['column']
        # new_value = json_blob['new_value']

        # if new_value == 'None':
        #     new_value = None
        pass
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "DailyPothole:\n\nError: {}".format(e),
        })