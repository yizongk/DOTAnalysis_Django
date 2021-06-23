from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import generic

from .models import *
from django.http import JsonResponse
import json
from django.core.exceptions import ObjectDoesNotExist


## Return a list of Operations that the client has access to. Returns not limited to 1 Operation, can be multiple.
def get_user_operation_and_boro_permission(username):
    try:
        permission_query = TblUserList.objects.using('DailyPothole').filter(
            username__exact=username
        ).order_by('operation_id')

        if permission_query.count() > 0:
            return {
                "success": True,
                "err": "",
                "operation_permission_list": [each.operation_id for each in permission_query],
                "operation_long_permission_list": [each.operation_id.operation for each in permission_query],
                "boro_permission_list": [each.boros_id for each in permission_query],
                "boro_long_permission_list": [each.boros_id.boro_long for each in permission_query],
            }
        return {
            "success": False,
            "err": "Cannot find any permissions for '{}'".format(username),
        }
    except Exception as e:
        print("Exception: DailyPothole: get_user_operation_and_boro_permission(): {}".format(e))
        return {
            "success": False,
            "err": 'Exception: DailyPothole: get_user_operation_and_boro_permission(): {}'.format(e),
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
                # user_permissions = get_user_operation_and_boro_permission(self.request.user)
                # if user_permissions['success'] == False:
                #     raise ValueError('get_user_operation_and_boro_permission() failed: {}'.format(user_permissions['err']))
                # else:
                #     allowed_operation_list = user_permissions['operation_permission_list']

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
def UpdatePotholesData(request):

    if request.method != "POST":
        return JsonResponse({
            "post_success": True,
            "post_msg": "{} HTTP request not supported".format(request.method),
        })


    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: UpdatePotholesData(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "UpdatePotholesData():\n\nUNAUTHENTICATE USER!",
            "post_data": None,
        })


    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "DailyPothole: UpdatePotholesData():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    try:
        type_of_pothole_info            = json_blob['type_of_pothole_info']
        date_of_repair_input            = json_blob['date_of_repair_input']
        operation_input                 = json_blob['select_operation_input']
        borough_input                   = json_blob['select_borough_input']
        pothole_crew_count_input        = json_blob['pothole_crew_count_input']
        regular_holes_repaired_input    = json_blob['regular_holes_repaired_input']
        today_pothole_crew_count_input  = json_blob['today_pothole_crew_count_input']
        today_date_input                = json_blob['today_date_input']

        date_input = None
        if type_of_pothole_info not in ['PotholeData', 'TodayCrewData']:
            raise ValueError("Unrecognized input for type_of_pothole_info: '{}'".format(type_of_pothole_info))

        if type_of_pothole_info == 'PotholeData':
            if date_of_repair_input is None:
                raise ValueError("date_of_repair_input cannot be None")

            if operation_input is None:
                raise ValueError("operation_input cannot be None")

            if borough_input is None:
                raise ValueError("borough_input cannot be None")

            date_input = date_of_repair_input

        if type_of_pothole_info == 'TodayCrewData':
            if today_date_input is None:
                raise ValueError("today_date_input cannot be None")

            date_input = today_date_input

        try:
            if pothole_crew_count_input is not None:
                pothole_crew_count_input        = int(pothole_crew_count_input)
        except ValueError as e:
            raise ValueError("pothole_crew_count_input '{}' cannot be converted into an Int".format(pothole_crew_count_input))
        except Exception as e:
            raise

        try:
            if regular_holes_repaired_input is not None:
                regular_holes_repaired_input        = int(regular_holes_repaired_input)
        except ValueError as e:
            raise ValueError("regular_holes_repaired_input '{}' cannot be converted into an Int".format(regular_holes_repaired_input))
        except Exception as e:
            raise

        try:
            if today_pothole_crew_count_input is not None:
                today_pothole_crew_count_input        = int(today_pothole_crew_count_input)
        except ValueError as e:
            raise ValueError("today_pothole_crew_count_input '{}' cannot be converted into an Int".format(today_pothole_crew_count_input))
        except Exception as e:
            raise


        is_admin = user_is_active_admin(remote_user)["isAdmin"]
        if not is_admin:
            user_permissions = get_user_operation_and_boro_permission(remote_user)
            if user_permissions['success'] == False:
                raise ValueError('get_user_operation_and_boro_permission() failed: {}'.format(user_permissions['err']))
            else:
                allowed_operation_list = user_permissions['operation_long_permission_list']
                allowed_boro_list = user_permissions['boro_long_permission_list']

            if (operation_input not in allowed_operation_list
                or borough_input not in allowed_boro_list):
                raise ValueError("'{}' does not have the permission to edit records related to '{}' and '{}'".format(remote_user, operation_input, borough_input))


        pothole_data = TblPotholeMaster.objects.using('DailyPothole').get(
            operation_id__operation__exact=operation_input,
            boros_id__boro_long__exact=borough_input,
            repair_date__exact=date_input,
        )


        user_obj = TblUserList.objects.using("DailyPothole").get(
            username__exact=remote_user,
        )

        from django.utils import timezone as tz, dateformat
        timestamp = tz.localtime(tz.now())

        if type_of_pothole_info == 'PotholeData':
            pothole_data.repair_crew_count = pothole_crew_count_input
            pothole_data.holes_repaired = regular_holes_repaired_input
            pothole_data.last_modified_stamp = timestamp
            pothole_data.last_modified_by_user_id = user_obj
            pothole_data.save()

        if type_of_pothole_info == 'TodayCrewData':
            pothole_data.daily_crew_count = today_pothole_crew_count_input
            pothole_data.last_modified_stamp = timestamp
            pothole_data.last_modified_by_user_id = user_obj
            pothole_data.save()

        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            # "type_of_pothole_info": type_of_pothole_info,
            # "date_of_repair_input": date_of_repair_input,
            # "operation_input": operation_input,
            # "borough_input": borough_input,
            # "pothole_crew_count_input": pothole_crew_count_input,
            # "regular_holes_repaired_input": regular_holes_repaired_input,
            # "today_pothole_crew_count_input": today_pothole_crew_count_input,
            # "today_date_input": today_date_input,
            # "timestamp": timestamp,
            # "user_id": user_obj.user_id,
            # "record": [pothole_data.pothole_master_id, pothole_data.repair_date, pothole_data.operation_id.operation_id, pothole_data.boros_id.boros_id, pothole_data.repair_crew_count, pothole_data.holes_repaired, pothole_data.daily_crew_count, pothole_data.last_modified_stamp, pothole_data.last_modified_by_user_id.user_id],
        })
    except ObjectDoesNotExist as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "DailyPothole:\n\nError: {}. For '{}', '{}' and '{}'".format(e, date_input, operation_input, borough_input),
        })
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "DailyPothole:\n\nError: {}".format(e),
            # "post_msg": "DailyPothole:\n\nError: {}. The exception type is:{}".format(e,  e.__class__.__name__),
        })