from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import generic
from django.http import HttpResponse, JsonResponse
from .models import *
import json

## Check if remote client is admin and is active
def user_is_active_admin(username):
    try:
        admin_query = Admins.objects.using('FleetDataCollection').filter(
            window_username=username,
            active=True, ## Filters for active Admins
        )
        if admin_query.count() > 0:
            return {
                "success": True,
                "err": "",
            }
        return {
            "success": False,
            "err": '{} is not an active Admin'.format(username),
        }
    except Exception as e:
        print("Exception: FleetDataCollection: user_is_active_admin(): {}".format(e))
        return {
            "success": None,
            "err": 'Exception: FleetDataCollection: user_is_active_admin(): {}'.format(e),
        }

## Return a list of WU that the client has access to
def get_allowed_list_of_wu(username):
    try:
        wu_query = WUPermissions.objects.using('FleetDataCollection').filter(
            window_username=username,
        ).order_by('wu')

        if wu_query.count() > 0:
            return {
                "success": True,
                "err": "",
                "wu_list": [each.wu for each in wu_query],
            }
        return {
            "success": False,
            "err": "Cannot find any WU permissions for '{}'".format(username),
        }
    except Exception as e:
        print("Exception: FleetDataCollection: get_allowed_list_of_wu(): {}".format(e))
        return {
            "success": False,
            "err": 'Exception: FleetDataCollection: get_allowed_list_of_wu(): {}'.format(e),
        }

## Return a list of PMS that the client has access to
def get_allowed_list_of_pms(username):
    allowed_wu_list_response = get_allowed_list_of_wu(username)
    if allowed_wu_list_response['success'] == False:
        return {
            "success": False,
            "err": "Error: FleetDataCollection: get_allowed_list_of_pms():\n\nFailed to get list of WU permissions: {}".format(allowed_wu_list_response['err']),
        }
    else:
        allowed_wu_list = allowed_wu_list_response['wu_list']


    pms_list_query = TblEmployees.objects.using('Orgchart').filter(
        wu__in=allowed_wu_list
    ).order_by('last_name')

    ## gives a list of pms
    pms_list_json_str = list(pms_list_query.values_list('pms', flat=True))

    return {
        "success": True,
        "err": None,
        "pms_list": pms_list_json_str,
    }

## Return a list of WU that the client has access to
def get_allowed_list_of_domiciles(username):
    try:
        domicile_query = DomicilePermissions.objects.using('FleetDataCollection').filter(
            window_username=username,
        ).order_by('domicile')

        if domicile_query.count() > 0:
            return {
                "success": True,
                "err": "",
                "domicile_list": [each.domicile for each in domicile_query],
            }
        return {
            "success": False,
            "err": "Cannot find any domicile permissions for '{}'".format(username),
        }
    except Exception as e:
        print("Exception: FleetDataCollection: get_allowed_list_of_domiciles(): {}".format(e))
        return {
            "success": False,
            "err": 'Exception: FleetDataCollection: get_allowed_list_of_domiciles(): {}'.format(e),
        }

## Return the domicile for the given unit_no
def get_domicile_for_unit_number(unit_no):
    try:
        domicile = NYC_DOTR_UNIT_MAIN.objects.using('M5').get(unit_no=unit_no).domicile
        return {
            "success": True,
            "err": "",
            "domicile": domicile,
        }
    except Exception as e:
        print("Exception: FleetDataCollection: get_domicile_for_unit_number(): {}, for unit_no '{}'".format(e, unit_no))
        return {
            "success": False,
            "err": "Exception: FleetDataCollection: get_domicile_for_unit_number(): {}, for unit_no '{}'".format(e, unit_no),
        }

## Return a list of Unit Numbers that the client has access to
def get_allowed_list_of_unit_numbers(username):
    permitted_domcile_list_obj = get_allowed_list_of_domiciles(username)
    if permitted_domcile_list_obj['success'] == False:
        return {
            "success": False,
            "err": "get_allowed_list_of_unit_numbers(): Cannot find any domicile permissions for '{}': {}".format(username, permitted_domcile_list_obj['err']),
        }
    else:
        permitted_domcile_list = permitted_domcile_list_obj['domicile_list']

    try:
        unit_number_query = NYC_DOTR_UNIT_MAIN.objects.using('M5').filter(
            domicile__in=permitted_domcile_list
        ).order_by('unit_no')

        if unit_number_query.count() > 0:
            return {
                "success": True,
                "err": "",
                "unit_number_list": [each.unit_no for each in unit_number_query],
            }
        return {
            "success": False,
            "err": "Cannot find any allowed unit_number for '{}'".format(username),
        }
    except Exception as e:
        print("Exception: FleetDataCollection: get_allowed_list_of_unit_numbers(): {}".format(e))
        return {
            "success": False,
            "err": 'Exception: FleetDataCollection: get_allowed_list_of_unit_numbers(): {}'.format(e),
        }

# Create your views here.
class HomePageView(TemplateView):
    template_name = 'FleetDataCollection.template.home.html'
    client_is_admin = False

    def get_context_data(self, **kwargs):
        try:
            ## Call the base implementation first to get a context
            context = super().get_context_data(**kwargs)
            self.client_is_admin = user_is_active_admin(self.request.user)["success"]
            context["client_is_admin"] = self.client_is_admin
            return context
        except Exception as e:
            context["client_is_admin"] = False
            return context

class AboutPageView(TemplateView):
    template_name = 'FleetDataCollection.template.about.html'

class ContactPageView(TemplateView):
    template_name = 'FleetDataCollection.template.contact.html'

class DriverAndTypeAssignmentConfirmationPageView(generic.ListView):
    template_name = 'FleetDataCollection.template.driverandtypeconfirmation.html'
    context_object_name = 'driver_type_assigment_entries'

    req_success = False
    err_msg = ""

    client_is_admin = False

    def get_queryset(self):
        ## Check for Active Admins
        is_active_admin = user_is_active_admin(self.request.user)
        if is_active_admin["success"] == True:
            self.client_is_admin = True
        else:
            self.req_success = False

        ## Get the core data
        try:
            if self.client_is_admin:
                driver_type_assigment_entries = M5DriverVehicleDataConfirmations.objects.using('FleetDataCollection').all().order_by('unit_number')
            else:
                allowed_unit_number_list_obj = get_allowed_list_of_unit_numbers(self.request.user)
                if allowed_unit_number_list_obj['success'] == False:
                    raise ValueError('get_allowed_list_of_unit_numbers() failed: {}'.format(allowed_unit_number_list_obj['err']))
                else:
                    allowed_unit_number_list = allowed_unit_number_list_obj['unit_number_list']

                driver_type_assigment_entries = M5DriverVehicleDataConfirmations.objects.using('FleetDataCollection').filter(
                    unit_number__in=allowed_unit_number_list,
                ).order_by('unit_number')
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: DriverAndTypeAssignmentConfirmationPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return M5DriverVehicleDataConfirmations.objects.none()

        self.req_success = True
        return driver_type_assigment_entries

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

## Returns a list of json objects with respect to client wu permission, each json object is a row in the tblEmployees, containing pms, first_name, last_name and wu
def GetPermittedEmpDataList(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: FleetDataCollection: GetPermittedEmpDataList(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "FleetDataCollection: GetPermittedEmpDataList():\n\nUNAUTHENTICATE USER!",
        })

    ## Get the data
    try:
        allowed_wu_list_response = get_allowed_list_of_wu(remote_user)
        if allowed_wu_list_response['success'] == False:
            return JsonResponse({
                "post_success": False,
                "post_msg": "Error: FleetDataCollection: GetPermittedEmpDataList():\n\nFailed to get list of WU permissions: {}".format(allowed_wu_list_response['err']),
            })
        else:
            allowed_wu_list = allowed_wu_list_response['wu_list']


        pms_list_query = TblEmployees.objects.using('Orgchart').filter(
            wu__in=allowed_wu_list,
            lv__in=['B', 'C', 'K', 'M', 'N', 'Q', 'R', 'S']  # Active Employee Lv Status
        ).order_by('last_name')

        pms_list_json_str = list(pms_list_query.values())

        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": pms_list_json_str,
        })
    except Exception as e:
        err_msg = "Exception: FleetDataCollection: GetPermittedEmpDataList(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })

## Returns a list of json objects, each json object is a row in the NYC_DOTR_UNIT_MAIN, containing make, model, unit_no, class1, and domicile
## Does not respect client wu permissions, because this api's purpose is to serve as the pms look up for the client-side JS DataTable
def GetEmpDataList(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: FleetDataCollection: GetEmpDataList(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "FleetDataCollection: GetEmpDataList():\n\nUNAUTHENTICATE USER!",
        })

    ## Get the data
    try:
        pms_list_query = TblEmployees.objects.using('Orgchart').filter(
            lv__in=['B', 'C', 'K', 'M', 'N', 'Q', 'R', 'S']  # Active Employee Lv Status
        ).order_by('last_name')

        pms_list_json_str = list(pms_list_query.values())

        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": pms_list_json_str,
        })
    except Exception as e:
        err_msg = "Exception: FleetDataCollection: GetEmpDataList(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })


## Returns a list of json objects, each json object is a row in the NYC_DOTR_UNIT_MAIN, containing make, model, unit_no, class1, and domicile
## Does not respect client domicile permissions, because this api's purpose is to serve as the m5 look up for the client-side JS DataTable
def GetM5DataList(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: FleetDataCollection: GetPermittedM5DataList(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "FleetDataCollection: GetPermittedM5DataList():\n\nUNAUTHENTICATE USER!",
        })

    ## Get the data
    try:
        m5_list_query = NYC_DOTR_UNIT_MAIN.objects.using('M5').all().order_by('unit_no')

        m5_list_json_str = list(m5_list_query.values())

        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": m5_list_json_str,
        })
    except Exception as e:
        err_msg = "Exception: FleetDataCollection: GetPermittedM5DataList(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })

## Update the PMS for a record
def UpdateM5DriverVehicleDataConfirmations(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: FleetDataCollection: UpdateM5DriverVehicleDataConfirmations(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "FleetDataCollection: UpdateM5DriverVehicleDataConfirmations():\n\nUNAUTHENTICATE USER!",
        })

    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "FleetDataCollection: UpdateM5DriverVehicleDataConfirmations():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    try:
        id = json_blob['id']
        table = json_blob['table']
        column = json_blob['column']
        new_value = json_blob['new_value']

        if new_value == 'None':
            new_value = None
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "FleetDataCollection:\n\nError: {}".format(e),
        })


    ## Save the data
    try:

        ## make sure client has permission to the domicile for current row
        domicile_for_row_obj = get_domicile_for_unit_number(id)
        if domicile_for_row_obj['success'] == False:
            raise ValueError( 'Exception: FleetDataCollection: get_domicile_for_unit_number(): {}'.format(domicile_for_row_obj['err']) )
        else:
            domicile_for_row = domicile_for_row_obj['domicile']

        permitted_domcile_list_obj = get_allowed_list_of_domiciles(remote_user)
        if permitted_domcile_list_obj['success'] == False:
            raise ValueError( 'Exception: FleetDataCollection: get_allowed_list_of_domiciles(): {}'.format(permitted_domcile_list_obj['err']) )
        else:
            permitted_domcile_list = permitted_domcile_list_obj['domicile_list']

        if domicile_for_row not in permitted_domcile_list:
            raise ValueError("Client '{}' does not have permission for Domicile '{}' for Unit No '{}'".format(remote_user, domicile_for_row, id))

        row = M5DriverVehicleDataConfirmations.objects.using('FleetDataCollection').get(unit_number=id)
        if column == 'PMS':
            ## make sure client has permission to the requested pms
            if new_value is not None:
                permitted_pms_list_obj = get_allowed_list_of_pms(remote_user)
                if permitted_pms_list_obj['success'] == False:
                    raise ValueError(permitted_pms_list_obj['err'])
                else:
                    permitted_pms_list = permitted_pms_list_obj['pms_list']

                if new_value not in permitted_pms_list:
                    raise ValueError("Client '{}' does not have permission for PMS '{}'".format(remote_user, new_value))

            row.pms = new_value
        elif column == 'Class2':
            row.class2 = new_value
        else:
            raise ValueError("FleetDataCollection: UpdateM5DriverVehicleDataConfirmations():\n\nError: Unsupported column: '{}'".format(column))

        row.save()
        return JsonResponse({
            "post_success": True,
            "post_msg": ""
        })
    except Exception as e:
        err_msg = "Exception: FleetDataCollection: UpdateM5DriverVehicleDataConfirmations(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })