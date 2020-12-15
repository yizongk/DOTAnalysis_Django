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

class AdminPanelPageView(generic.ListView):
    template_name = 'FleetDataCollection.template.adminpanel.html'

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
            self.err_msg = "AdminPanelPageView(): get_queryset(): {} is not an Admin and is not authorized to see this page".format(self.request.user)
            print(self.err_msg)
            return

        self.req_success = True

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

    client_is_admin = None
    is_active_admin = user_is_active_admin(request.user)
    if is_active_admin["success"] == True:
        client_is_admin = True
    elif is_active_admin["success"] == False:
        client_is_admin = False
    else:
        return JsonResponse({
            "post_success": False,
            "post_msg": "FleetDataCollection: GetPermittedEmpDataList(): Unhandled case: user_is_active_admin() returned a none boolean."
        })

    ## Get the data
    try:
        if client_is_admin == True:
            pms_list_query = TblEmployees.objects.using('Orgchart').filter(
                lv__in=['B', 'C', 'K', 'M', 'N', 'Q', 'R', 'S']  # Active Employee Lv Status
            ).order_by('last_name')
        else:
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
def GetEmpLookUpDataList(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: FleetDataCollection: GetEmpLookUpDataList(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "FleetDataCollection: GetEmpLookUpDataList():\n\nUNAUTHENTICATE USER!",
        })

    ## Get the data
    try:
        pms_list_query = TblEmployees.objects.using('Orgchart').filter(
            lv__in=['B', 'C', 'K', 'M', 'N', 'Q', 'R', 'S']  # Active Employee Lv Status
        ).order_by('last_name')

        pms_list_json_str = list(pms_list_query.values(
            'pms'
            ,'first_name'
            ,'last_name'
            ,'lv'
            ,'wu'
            ,'wu__subdiv'
        ))

        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": pms_list_json_str,
        })
    except Exception as e:
        err_msg = "Exception: FleetDataCollection: GetEmpLookUpDataList(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })


## Returns a list of json objects, each json object is a row in the NYC_DOTR_UNIT_MAIN, containing make, model, unit_no, class1, and domicile
## Does not respect client domicile permissions, because this api's purpose is to serve as the m5 look up for the client-side JS DataTable
def GetM5LookUpDataList(request):
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

    client_is_admin = None
    is_active_admin = user_is_active_admin(request.user)
    if is_active_admin["success"] == True:
        client_is_admin = True
    elif is_active_admin["success"] == False:
        client_is_admin = False
    else:
        return JsonResponse({
            "post_success": False,
            "post_msg": "FleetDataCollection: UpdateM5DriverVehicleDataConfirmations(): Unhandled case: user_is_active_admin() returned a none boolean."
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

        ## If client is not admin, make sure client has permission to the domicile for current row
        if client_is_admin == True:
            ## Important that you check client_is_admin == True, since it could possible be False or None, where the former means client is not admin, and the latter means something functions failed and was unhandled.
            pass
        else:
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
                ## If client is not admin, make sure client has permission to the pms for current row
                if client_is_admin == True:
                    ## Important that you check client_is_admin == True, since it could possible be False or None, where the former means client is not admin, and the latter means something functions failed and was unhandled.
                    pass
                else:
                    permitted_pms_list_obj = get_allowed_list_of_pms(remote_user)
                    if permitted_pms_list_obj['success'] == False:
                        raise ValueError(permitted_pms_list_obj['err'])
                    else:
                        permitted_pms_list = permitted_pms_list_obj['pms_list']

                    if new_value not in permitted_pms_list:
                        raise ValueError("Client '{}' does not have permission for PMS '{}'".format(remote_user, new_value))

            row.pms = new_value
        elif column == 'Class2':
            if new_value == 'Commuter':
                row.class2 = True
            elif new_value == 'Non-Commuter':
                row.class2 = False
            else:
                row.class2 = None
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











class WuPermissionsPanelPageView(generic.ListView):
    template_name = 'FleetDataCollection.template.wupermissionspanel.html'
    context_object_name = 'permission_data_entries'

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
            self.err_msg = "WuPermissionsPanelPageView(): get_queryset(): {} is not an Admin and is not authorized to see this page".format(self.request.user)
            print(self.err_msg)
            return WUPermissions.objects.none()

        ## Get the permissions data
        try:
            permission_data_entries = WUPermissions.objects.using('FleetDataCollection').all().order_by('window_username')
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: WuPermissionsPanelPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return WUPermissions.objects.none()

        self.req_success = True
        return permission_data_entries

    def get_context_data(self, **kwargs):
        try:
            ## Call the base implementation first to get a context
            context = super().get_context_data(**kwargs)

            ## Finally, setting the context variables
            ## Add my own variables to the context for the front end to shows
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

# ## Post request - for single cell edits
# def WUPermissionsPanelApiUpdateData(request):
#     ## Read the json request body
#     try:
#         json_blob = json.loads(request.body)
#     except Exception as e:
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "Error: WUPermissionsPanelApiUpdateData():\n\nUnable to load request.body as a json object: {}".format(e),
#         })

#     try:
#         id = json_blob['id']
#         table = json_blob['table']
#         column = json_blob['column']
#         new_value = json_blob['new_value']
#     except Exception as e:
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "Error: WUPermissionsPanelApiUpdateData():\n\nError: {}".format(e),
#         })

#     ## Authenticate User
#     remote_user = None
#     if request.user.is_authenticated:
#         remote_user = request.user.username
#     else:
#         print('Warning: WUPermissionsPanelApiUpdateData(): UNAUTHENTICATE USER!')
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "WUPermissionsPanelApiUpdateData():\n\nUNAUTHENTICATE USER!",
#             "post_data": None,
#         })

#     ## Check active user
#     is_active_user = user_is_active_user(request.user)
#     if is_active_user["success"] == True:
#         pass
#     else:
#         print("WUPermissionsPanelApiUpdateData(): {}".format(is_active_user["err"]))
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "WUPermissionsPanelApiUpdateData(): {}".format(is_active_user["err"]),
#             "post_data": None,
#         })

#     ## Check active admin
#     is_active_admin = user_is_active_admin(request.user)
#     if is_active_admin["success"] == True:
#         pass
#     else:
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "WUPermissionsPanelApiUpdateData(): {}".format(is_active_admin["err"]),
#             "post_data": None,
#         })

#     ## Save the data
#     if table == "Users":

#         ## Make sure new_value is convertable to its respective data type
#         if column == "Active_User":
#             try:
#                 new_value = bool(new_value)
#             except Exception as e:
#                 print("Error: WUPermissionsPanelApiUpdateData(): Unable to convert new_value '{}' to bool type, did not save the value".format(new_value))
#                 return JsonResponse({
#                     "post_success": False,
#                     "post_msg": "Error: WUPermissionsPanelApiUpdateData():\n\nUnable to convert new_value '{}' to bool type, did not save the value".format(new_value),
#                 })
#         else:
#             try:
#                 new_value = str(new_value)
#             except Exception as e:
#                 print("Error: WUPermissionsPanelApiUpdateData(): Unable to convert new_value '{}' to str type, did not save the value".format(new_value))
#                 return JsonResponse({
#                     "post_success": False,
#                     "post_msg": "Error: WUPermissionsPanelApiUpdateData():\n\nUnable to convert new_value '{}' to str type, did not save the value".format(new_value),
#                 })

#         ## Save the value
#         try:
#             row = WUPermissions.objects.get(user_permission_id=id)
#             if column == "Login":
#                 try:
#                     user_obj = Users.objects.get(login=new_value, active_user=True) ## Will throw exception if no user is found with the criteria: "Users matching query does not exist.""
#                     row.user = user_obj

#                     row.save()

#                     # # Temp
#                     # return JsonResponse({
#                     #     "post_success": False,
#                     #     "post_msg": "trying to save: '{}'".format(new_value),
#                     # })

#                     print("Api Log: WUPermissionsPanelApiUpdateData(): Client '{}' has successfully updated User_Permissions. For User_Permission_ID '{}' updated the User to '{}'".format(remote_user, id, new_value))
#                     return JsonResponse({
#                         "post_success": True,
#                         "post_msg": "",
#                     })
#                 except Exception as e:
#                     print("Error: WUPermissionsPanelApiUpdateData(): While trying to update a User Permission record to login '{}': {}".format(new_value, e))
#                     return JsonResponse({
#                         "post_success": False,
#                         "post_msg": "Error: WUPermissionsPanelApiUpdateData():\n\nWhile trying to a User Permission record to login '{}': {}".format(new_value, e),
#                     })
#         except Exception as e:
#             print("Error: WUPermissionsPanelApiUpdateData(): While trying to update a User Permission record to login '{}': {}".format(new_value, e))
#             return JsonResponse({
#                 "post_success": False,
#                 "post_msg": "Error: WUPermissionsPanelApiUpdateData():\n\nWhile trying to a User Permission record to login '{}': {}".format(new_value, e),
#             })

#     # elif table == "":
#     #     pass


#     print("Warning: WUPermissionsPanelApiUpdateData(): Did not know what to do with the request. The request:\n\nid: '{}'\n table: '{}'\n column: '{}'\n new_value: '{}'\n".format(id, table, column, new_value))
#     return JsonResponse({
#         "post_success": False,
#         "post_msg": "Warning: WUPermissionsPanelApiUpdateData():\n\nDid not know what to do with the request. The request:\n\nid: '{}'\n table: '{}'\n column: '{}'\n new_value: '{}'\n".format(id, table, column, new_value),
#     })

# ## For form add row
# def WUPermissionsPanelApiAddRow(request):
#     """
#         Expects the post request to post a JSON object, and that it will contain login_selection and category_selection. Like so:
#         {
#             login_selection: "Some value",
#             category_selection: "Some other value"
#         }
#         Will create a new row in the Permissions table with the selected login and category
#     """

#     ## Authenticate User
#     remote_user = None
#     if request.user.is_authenticated:
#         remote_user = request.user.username
#     else:
#         print('Warning: WUPermissionsPanelApiAddRow(): UNAUTHENTICATE USER!')
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "WUPermissionsPanelApiAddRow():\n\nUNAUTHENTICATE USER!",
#         })

#     ## Check active user
#     is_active_user = user_is_active_user(request.user)
#     if is_active_user["success"] == True:
#         pass
#     else:
#         print("WUPermissionsPanelApiAddRow(): {}".format(is_active_user["err"]))
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "WUPermissionsPanelApiAddRow(): {}".format(is_active_user["err"]),
#         })

#     ## Check active admin
#     is_active_admin = user_is_active_admin(request.user)
#     if is_active_admin["success"] == True:
#         pass
#     else:
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "WUPermissionsPanelApiAddRow(): {}".format(is_active_admin["err"]),
#         })

#     ## Read the json request body
#     try:
#         json_blob = json.loads(request.body)
#     except Exception as e:
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "Error: WUPermissionsPanelApiAddRow():\n\nUnable to load request.body as a json object: {}".format(e),
#         })

#     ## Check login_selection and category_selection is not empty string
#     try:
#         login_selection = json_blob['login_selection']
#         category_selection = json_blob['category_selection']

#         if login_selection == "":
#             return JsonResponse({
#                 "post_success": False,
#                 "post_msg": "login_selection cannot be an empty string".format(login_selection, category_selection),
#             })

#         if category_selection == "":
#             return JsonResponse({
#                 "post_success": False,
#                 "post_msg": "category_selection cannot be an empty string".format(login_selection, category_selection),
#             })
#     except Exception as e:
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "Error: WUPermissionsPanelApiAddRow():\n\nThe POSTed json obj does not have the following variable: {}".format(e),
#         })

#     ## Check that the login_selection and category_selection exists
#     try:
#         if not Users.objects.filter(login__exact=login_selection, active_user__exact=True).exists():
#             return JsonResponse({
#                 "post_success": False,
#                 "post_msg": "'{}' doesn't exists or it's not an active user".format(login_selection),
#             })
#     except Exception as e:
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "Error: WUPermissionsPanelApiAddRow(): {}".format(e),
#         })

#     try:
#          if not Category.objects.filter(category_name__exact=category_selection).exists():
#             return JsonResponse({
#                 "post_success": False,
#                 "post_msg": "'{}' doesn't exists as a Category".format(category_selection),
#             })
#     except Exception as e:
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "Error: WUPermissionsPanelApiAddRow(): {}".format(e),
#         })

#     ## Check for duplication of login and category
#     try:
#         if WUPermissions.objects.filter(user__login__exact=login_selection, category__category_name__exact=category_selection).exists():
#             return JsonResponse({
#                 "post_success": False,
#                 "post_msg": "'{}' already has access to '{}'".format(login_selection, category_selection),
#             })
#     except Exception as e:
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "Error: WUPermissionsPanelApiAddRow(): {}".format(e),
#         })

#     ## Create the row!
#     try:
#         user_obj = Users.objects.get(login=login_selection, active_user=True)
#         category_obj = Category.objects.get(category_name=category_selection)
#         new_permission = WUPermissions(user=user_obj, category=category_obj)
#         new_permission.save()
#     except Exception as e:
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "Error: WUPermissionsPanelApiAddRow(): {}".format(e),
#         })

#     return JsonResponse({
#         "post_success": True,
#         "post_msg": "",
#         "permission_id": new_permission.user_permission_id,
#         "first_name": user_obj.first_name,
#         "last_name": user_obj.last_name,
#         "active_user": user_obj.active_user,
#         "login": user_obj.login,
#         "category_name": category_obj.category_name,
#     })

# ## For JS datatable delete row
# def WUPermissionsPanelApiDeleteRow(request):
#     """
#         Expects the post request to post a JSON object, and that it will contain user_permission_id. Like so:
#         {
#             user_permission_id: "Some value"
#         }
#         Will delete row in the Permissions table with the given user_permission_id
#     """

#     ## Authenticate User
#     remote_user = None
#     if request.user.is_authenticated:
#         remote_user = request.user.username
#     else:
#         print('Warning: WUPermissionsPanelApiDeleteRow(): UNAUTHENTICATE USER!')
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "WUPermissionsPanelApiDeleteRow():\n\nUNAUTHENTICATE USER!",
#         })

#     ## Check active user
#     is_active_user = user_is_active_user(request.user)
#     if is_active_user["success"] == True:
#         pass
#     else:
#         print("WUPermissionsPanelApiDeleteRow(): {}".format(is_active_user["err"]))
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "WUPermissionsPanelApiDeleteRow(): {}".format(is_active_user["err"]),
#         })

#     ## Check active admin
#     is_active_admin = user_is_active_admin(request.user)
#     if is_active_admin["success"] == True:
#         pass
#     else:
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "WUPermissionsPanelApiDeleteRow(): {}".format(is_active_admin["err"]),
#         })

#     ## Read the json request body
#     try:
#         json_blob = json.loads(request.body)
#     except Exception as e:
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "Error: WUPermissionsPanelApiDeleteRow():\n\nUnable to load request.body as a json object: {}".format(e),
#         })

#     ## Make sure user_permission_id is convertable to a unsign int
#     try:
#         user_permission_id = json_blob['user_permission_id']

#         try:
#             user_permission_id = int(user_permission_id)
#         except Exception as e:
#             return JsonResponse({
#                 "post_success": False,
#                 "post_msg": "user_permission_id cannot be converted to an int: '{}'".format(user_permission_id),
#             })

#         if user_permission_id <= 0:
#             return JsonResponse({
#                 "post_success": False,
#                 "post_msg": "user_permission_id is less than or equal to zero: '{}'".format(user_permission_id),
#             })
#     except Exception as e:
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "Error: WUPermissionsPanelApiDeleteRow():\n\nThe POSTed json obj does not have the following variable: {}".format(e),
#         })

#     ## Remove the permission row
#     try:
#         permission_row = WUPermissions.objects.get(user_permission_id=user_permission_id)
#         permission_row.delete()
#     except Exception as e:
#         return JsonResponse({
#             "post_success": False,
#             "post_msg": "Error: WUPermissionsPanelApiDeleteRow():\n\nFailed to remove user_permission_id '{}' from database: '{}'".format(user_permission_id, e),
#         })

#     return JsonResponse({
#         "post_success": True,
#         "post_msg": "",
#     })
