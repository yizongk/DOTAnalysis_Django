from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import generic
from django.http import HttpResponse, JsonResponse
from .models import *
from django.db.models import Min, Q, F, Value, Case, When
from django.db.models.functions import Concat
import json
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from datetime import timedelta


# Create your views here.


## Check if remote user is admin and is active
def user_is_active_admin(username):
    try:
        admin_query = TblUsers.objects.using('OrgChartWrite').filter(
            windows_username=username
            ,active=True
            ,is_admin=True
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


class HomePageView(TemplateView):
    template_name = 'OrgChartPortal.template.home.html'
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
    template_name = 'OrgChartPortal.template.about.html'


class ContactPageView(TemplateView):
    template_name = 'OrgChartPortal.template.contact.html'


def get_allowed_list_of_wu(username):
    try:
        wu_query = TblPermissionsWorkUnit.objects.using('OrgChartRead').filter(
            user_id__windows_username=username
            ,user_id__active=True
        ).order_by('wu__wu')

        if wu_query.count() > 0:
            return {
                "success": True,
                "err": "",
                "wu_list": [each.wu.wu for each in wu_query],
            }
        return {
            "success": False,
            "err": "Cannot find any WU permissions for '{}'".format(username),
        }
    except Exception as e:
        print("Exception: OrgChartPortal: get_allowed_list_of_wu(): {}".format(e))
        return {
            "success": False,
            "err": 'Exception: OrgChartPortal: get_allowed_list_of_wu(): {}'.format(e),
        }


def get_active_tblemployee_qryset():
    return TblEmployees.objects.using('OrgChartWrite').filter(
        lv__in=[
            'B'
            ,'C'
            ,'K'
            ,'M'
            ,'N'
            ,'Q'
            ,'R'
            ,'S'
        ]
    )


def get_active_emp_qryset(
        fields_list = [  ## specifiy the list of columns that you want
            'pms'
            ,'lv'
            ,'wu__wu'
            ,'last_name'
            ,'first_name'
            ,'civil_title'
            ,'supervisor_pms__last_name'
            ,'supervisor_pms__first_name'
            ,'office_title'
            ,'actual_site_id__site'
            ,'actual_floor_id__floor'
            ,'actual_site_type_id__site_type'
            ,'abc_group'
        ]
        ,custom_annotate_fct = None
    ):
    '''
    @fields_list
        A list of fields that is returned in the final qryset. Must also include any new field names that is created in the function given in @custom_annotate_fct

    @custom_annotate_fct:
        The function that will be called to annotate the qryset for additional fields of data.
        The new annotated field names must also be in @fields_list, otherwise those new fields won't be part of the final qryset that is returned.

        Expects only one argument called 'qryset' which is must be a Django Queryset.
        Example:
            def annotate_fct(qryset):
                qryset = qryset.annotate(supervisor_pms__full_name=Concat( F('supervisor_pms__last_name'), Value(', '), F('supervisor_pms__first_name') ))
                qryset = qryset.annotate(emp_full_name_and_pms=...)
                qryset = qryset.annotate(...)
                return qryset
                ...

            final_qryset = get_active_emp_qryset(
                ...
                fields_list = ['supervisor_pms__full_name', 'emp_full_name_and_pms', ...]
                custom_annotate_fct = annotate_fct
                ...
            )
    '''

    qryset = get_active_tblemployee_qryset()

    if custom_annotate_fct is not None:
        qryset = custom_annotate_fct(qryset)

    ## To speed up the query, need to specify only the columns that is needed, so that django do a one-time query of the entire related dataset.
    return qryset.values(*fields_list)


'''
Create an instance of this class whenever you need to update data on an exiting employee in tblEmployees
It will update the employee and then keep a history of the change.
Pass in the correct params, and call save().

@updated_by_pms = The PMS of the client attempting to make an update to an employee row, calling function should have a windows username to lookup the PMS with.
@updated_to_pms = The PMS of the employee row that is being updated.
@new_value      = The new value that is updating to the employee row.
@column_name    = The column name that the new value belongs to on the employee row.

When you call save():
    * An atomic database transaction is garanteed.
    * A current timestamp is also generated.
    * Then with all the data, it will be inserted into  tblChanges.
    * If the new value is the same as the old value, this will return False.
    * Returns true if all is successful.
    * Raise the error if any exception is present.
'''
class EmppUpdateAndTrack:
    def __init__(
        self
        ,updated_by_pms = None
        ,updated_to_pms = None
        ,new_value      = None
        ,column_name    = None
    ):
        self.updated_by_pms = updated_by_pms
        self.updated_to_pms = updated_to_pms
        self.new_value      = new_value
        self.column_name    = column_name

        self.valid_column_names = [
            'SupervisorPMS'
            ,'OfficeTitle'
            ,'ActualSiteId'
            ,'ActualFloorId'
            ,'ActualSiteTypeId'
        ]


    def save(self):
        try:
            if self.updated_by_pms is None: raise ValueError("updated_by_pms cannot be None.")
            if self.updated_to_pms is None: raise ValueError("updated_to_pms cannot be None.")
            if self.new_value is None:      raise ValueError("new_value cannot be None.")
            if self.column_name is None:    raise ValueError("column_name cannot be None.")

            ## timezone.now() is timezone awared, so when entered into the sql server, it will be stored as a UTC time. I need to trick it into storing EST time in sql server, so a manually -5 hour difference is applied here.
            updated_on = timezone.now() - timezone.timedelta(hours=5)
            if updated_on is None:
                raise ValueError("updated_on cannot be None.")

            if self.column_name not in self.valid_column_names:
                raise ValueError(f"{self.column_name} is not a valid column name.")


            ## Find the target employee row
            try:
                employee_row = get_active_tblemployee_qryset().get(pms__exact=self.updated_to_pms)
            except ObjectDoesNotExist as e:
                raise ValueError(f"The PMS '{self.updated_to_pms}' is either inactive or doesn't exists")


            ## Implementation of specific column updates
            if self.column_name == 'SupervisorPMS':
                try:
                    new_supervisor_obj = get_active_tblemployee_qryset()
                    new_supervisor_obj = new_supervisor_obj.get(pms__exact=self.new_value)
                except ObjectDoesNotExist as e:
                    raise ValueError(f"The Supervisor PMS '{self.new_value}' is either inactive or doesn't exist")

                ## Data validation
                if employee_row.supervisor_pms is not None and employee_row.supervisor_pms.pms == new_supervisor_obj.pms:
                    ## Return False because new value is same as old value
                    return False
                elif employee_row.pms == new_supervisor_obj.pms:
                    raise ValueError(f"A person cannot be their own supervisor")
                else:
                    employee_row.supervisor_pms = new_supervisor_obj

            elif self.column_name == 'OfficeTitle':
                ## Data validation
                if employee_row.office_title is not None and employee_row.office_title == self.new_value:
                    return False
                else:
                    employee_row.office_title = self.new_value

            elif self.column_name == 'ActualSiteId':
                try:
                    new_site_obj = TblDOTSites.objects.using('OrgChartWrite').get(site_id__exact=self.new_value)
                except ObjectDoesNotExist as e:
                    raise ValueError(f"The Site Id '{self.new_value}' doesn't exist")

                ## Data validation
                if employee_row.actual_site_id is not None and employee_row.actual_site_id.site_id == new_site_obj.site_id:
                    ## Return False because new value is same as old value
                    return False
                else:
                    employee_row.actual_site_id = new_site_obj

            elif self.column_name == 'ActualFloorId':
                try:
                    new_floor_obj = TblDOTSiteFloors.objects.using('OrgChartWrite').get(floor_id__exact=self.new_value)
                except ObjectDoesNotExist as e:
                    raise ValueError(f"The Floor Id '{self.new_value}' doesn't exist")

                ## Data validation
                if employee_row.actual_floor_id is not None and employee_row.actual_floor_id.floor_id == new_floor_obj.floor_id:
                    ## Return False because new value is same as old value
                    return False
                elif employee_row.actual_site_id.site_id != new_floor_obj.site_id.site_id:
                    ## Floor_Id must be associated with employee's current Site_Id
                    raise ValueError(f"Floor ({new_floor_obj.floor}-{self.new_value}) is not a valid floor for ({employee_row.actual_site_id.site}-{employee_row.actual_site_id.site_id})")
                else:
                    employee_row.actual_floor_id = new_floor_obj

            elif self.column_name == 'ActualSiteTypeId':
                try:
                    new_site_type_obj = TblDOTSiteTypes.objects.using('OrgChartWrite').get(site_type_id__exact=self.new_value)
                except ObjectDoesNotExist as e:
                    raise ValueError(f"The Site Type Id '{self.new_value}' doesn't exist")

                ## Data validation
                try:
                    site_and_floor_validation_obj = site_type_validation_obj = TblDOTSiteFloorSiteTypes.objects.using('OrgChartWrite').filter(
                        floor_id__site_id__site_id__exact   = employee_row.actual_site_id.site_id
                        ,floor_id__floor_id__exact          = employee_row.actual_floor_id.floor_id
                    )

                    site_type_validation_obj = TblDOTSiteFloorSiteTypes.objects.using('OrgChartWrite').filter(
                        floor_id__site_id__site_id__exact   = employee_row.actual_site_id.site_id
                        ,floor_id__floor_id__exact          = employee_row.actual_floor_id.floor_id
                        ,site_type_id__site_type_id__exact  = self.new_value
                    )
                except Exception as e:
                    raise ValueError(f"Failed to obtain data validation objects: {e}")

                if employee_row.actual_site_type_id is not None and employee_row.actual_site_type_id.site_type_id == new_site_type_obj.site_type_id:
                    ## Return False because new value is same as old value
                    return False
                elif site_and_floor_validation_obj.count() == 0:
                    ## Employee's current Site_Id and Floor_Id must be associated with each other.
                    raise ValueError(f"Invalid Site ({employee_row.actual_site_id.site}-{employee_row.actual_site_id.site_id}) and Floor ({employee_row.actual_floor_id.floor}-{employee_row.actual_floor_id.floor_id}) combination, please fix those first before entering Site Type.")
                elif site_type_validation_obj.count() == 0:
                    ## Site_Type_Id must be associated with employee's current Site_Id and Floor_Id
                    raise ValueError(f"Site Type ({new_site_type_obj.site_type}-{self.new_value}) is not a valid site type for ({employee_row.actual_site_id.site_id}-{employee_row.actual_site_id.site}) and ({employee_row.actual_floor_id.floor_id}-{employee_row.actual_floor_id.floor})")
                else:
                    employee_row.actual_site_type_id = new_site_type_obj

            else:
                raise ValueError(f"{self.column_name} is not an editable column")


            # Save the data, and track the change history, in a single atomic transaction
            try:
                with transaction.atomic(using='OrgChartWrite'):
                    employee_row.save(using='OrgChartWrite')

                    change_record_row = TblChanges(
                        updated_on      = updated_on
                        ,updated_by_pms = self.updated_by_pms
                        ,updated_to_pms = self.updated_to_pms
                        ,new_value      = self.new_value
                        ,column_name    = self.column_name
                    )

                    change_record_row.save(using='OrgChartWrite')
            except Exception as e:
                raise

            return True
        except Exception as e:
            raise ValueError(f"Class EmppUpdateAndTrack: save(): {e}")


def UpdateEmployeeData(request):

    if request.method != "POST":
        return JsonResponse({
            "post_success": False,
            "post_msg": "UpdateEmployeeData(): {} HTTP request not supported".format(request.method),
        })

    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: UpdateEmployeeData(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "UpdateEmployeeData():\n\nUNAUTHENTICATE USER!",
            "post_data": None,
        })

    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "UpdateEmployeeData():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    try:
        if (
            'to_pms' not in json_blob
            or 'column_name' not in json_blob
            or 'new_value' not in json_blob
        ):
            raise ValueError("missing one or more of the required parameters (to_pms, column_name and new_value)")

        to_pms      = json_blob['to_pms']
        column_name = json_blob['column_name']
        new_value   = json_blob['new_value']

        # Front end column names mapping to backend field names
        valid_editable_column_names_mapping = {
            'Supervisor'        : 'SupervisorPMS'
            ,'OfficeTitle'      : 'OfficeTitle'
            ,'ActualSite'       : 'ActualSiteId'
            ,'ActualFloor'      : 'ActualFloorId'
            ,'ActualSiteType'   : 'ActualSiteTypeId'
        }

        if column_name not in list(valid_editable_column_names_mapping.keys()):
            raise ValueError(f"{column_name} is not an editable column")

        if new_value == '':
            raise ValueError(f"new_value for {column_name} cannot be None or empty text")

        # Check for permission to edit the target employee row
        is_admin = user_is_active_admin(remote_user)["isAdmin"]
        if not is_admin:
            wu_permissions = get_allowed_list_of_wu(remote_user)
            if wu_permissions['success']:
                allowed_wu_list = wu_permissions['wu_list']
            else:
                raise ValueError(f"get_allowed_list_of_wu() failed: {wu_permissions['err']}")

            try:
                employee_row = get_active_tblemployee_qryset().get(pms__exact=to_pms)
            except ObjectDoesNotExist as e:
                raise ValueError(f"The PMS '{to_pms}' is either inactive or doesn't exists")
            if employee_row.wu.wu not in allowed_wu_list:
                raise ValueError(f"user doesn't not have permission to edit {employee_row.pms}'s record (Need permission to their WU)")


        ## Get the client's user obj from database
        try:
            remote_user_obj = TblUsers.objects.using('OrgChartWrite').get(windows_username__exact=remote_user)
        except ObjectDoesNotExist as e:
            raise ValueError(f"The client '{remote_user}' is not a user of the system")


        atomic_update = EmppUpdateAndTrack(
            updated_by_pms  = remote_user_obj.pms.pms
            ,updated_to_pms = to_pms
            ,new_value      = new_value
            ,column_name    = valid_editable_column_names_mapping[column_name]
        )
        if not atomic_update.save():
            raise ValueError(f"No change in data, no update needed.")


    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "UpdateEmployeeData():\n\nError: {}".format(e),
            # "post_msg": "UpdateEmployeeData():\n\nError: {}. The exception type is:{}".format(e,  e.__class__.__name__),
        })

    return JsonResponse({
        "post_success": True,
        "post_msg": None,
    })


class EmpGridPageView(generic.ListView):
    template_name                   = 'OrgChartPortal.template.empgrid.html'
    context_object_name             = 'emp_entries'

    req_success                     = False
    err_msg                         = ""

    client_is_admin                 = False

    emp_entry_columns_json          = None
    emp_entries_json                = None
    supervisor_dropdown_list_json   = None
    site_dropdown_list_json         = None
    site_floor_dropdown_list_json   = None
    site_type_dropdown_list_json    = None

    def get_queryset(self):
        ## Check for Active Admins
        self.client_is_admin = user_is_active_admin(self.request.user)['isAdmin']

        ## Get the core data
        try:
            # def annotate_sup_full_name(qryset):
            #     return qryset.annotate(
            #         annotated__supervisor_full_name=Case(
            #             When(
            #                 supervisor_pms__pms__isnull=False
            #                 ,then=Concat( F('supervisor_pms__last_name'), Value(', '), F('supervisor_pms__first_name') )
            #             )
            #             ,default=None
            #         )
            #     )

            def annotate_emp_full_name(qryset):
                return qryset.annotate(
                    annotated__full_name=Concat( F('last_name'), Value(', '), F('first_name') )
                )

            ag_grid_col_def = [ ## Need to format this way for AG Grid
                {'headerName': 'PMS'              , 'field': 'pms'                                  , 'suppressMovable': True , 'lockPinned': True , 'pinned': 'left'}
                ,{'headerName': 'LastName'        , 'field': 'last_name'                            , 'suppressMovable': True , 'lockPinned': True , 'pinned': 'left'}
                ,{'headerName': 'FirstName'       , 'field': 'first_name'                           , 'suppressMovable': True , 'lockPinned': True , 'pinned': 'left'}
                ,{'headerName': 'Lv'              , 'field': 'lv'                                   , 'suppressMovable': True , 'lockPinned': True , 'pinned': 'left'}
                ,{'headerName': 'WU'              , 'field': 'wu__wu'                               , 'suppressMovable': True , 'lockPinned': True , 'pinned': 'left'}
                ,{'headerName': 'Title'           , 'field': 'civil_title'                          , 'suppressMovable': True , 'lockPinned': True , 'pinned': 'left'}
                ,{'headerName': 'Supervisor'      , 'field': 'supervisor_pms__pms'                  , 'suppressMovable': True , 'lockPinned': True}
                ,{'headerName': 'OfficeTitle'     , 'field': 'office_title'                         , 'suppressMovable': True , 'lockPinned': True}
                ,{'headerName': 'ActualSite'      , 'field': 'actual_site_id__site_id'              , 'suppressMovable': True , 'lockPinned': True}
                ,{'headerName': 'ActualFloor'     , 'field': 'actual_floor_id__floor_id'            , 'suppressMovable': True , 'lockPinned': True}
                ,{'headerName': 'ActualSiteType'  , 'field': 'actual_site_type_id__site_type_id'    , 'suppressMovable': True , 'lockPinned': True}
            ]

            fields_list = [each['field'] for each in ag_grid_col_def]

            if self.client_is_admin:
                emp_entries = get_active_emp_qryset(
                    fields_list=fields_list
                    # ,custom_annotate_fct=annotate_sup_full_name
                ).order_by('wu__wu', 'last_name')
            else:
                allowed_wu_list_obj = get_allowed_list_of_wu(self.request.user)
                if allowed_wu_list_obj['success'] == False:
                    raise ValueError(f"get_allowed_list_of_wu() failed: {allowed_wu_list_obj['err']}")
                else:
                    allowed_wu_list = allowed_wu_list_obj['wu_list']

                emp_entries = get_active_emp_qryset(
                    fields_list=fields_list
                    # ,custom_annotate_fct=annotate_sup_full_name
                ).filter(
                    wu__wu__in=allowed_wu_list,
                ).order_by('wu__wu', 'last_name')

            supervisor_dropdown_list = get_active_emp_qryset(
                fields_list=[
                    'pms'
                    ,'annotated__full_name'
                ]
                ,custom_annotate_fct=annotate_emp_full_name
            ).order_by('last_name')

            site_dropdown_list = TblDOTSites.objects.using('OrgChartRead').values(
                'site_id'
                ,'site'
            ).order_by('site')

            site_floor_dropdown_list = TblDOTSiteFloors.objects.using('OrgChartRead').values(
                'floor_id'
                ,'site_id'
                ,'floor'
            ).order_by('floor')

            site_type_dropdown_list = TblDOTSiteFloorSiteTypes.objects.using('OrgChartRead').values(
                'site_type_id__site_type_id'
                ,'site_type_id__site_type'
                ,'floor_id__floor_id'
                ,'floor_id__site_id'
            ).order_by('site_type_id__site_type')

            import json
            from django.core.serializers.json import DjangoJSONEncoder

            self.emp_entry_columns_json         = json.dumps(list(ag_grid_col_def)          , cls=DjangoJSONEncoder)
            self.emp_entries_json               = json.dumps(list(emp_entries)              , cls=DjangoJSONEncoder)
            self.supervisor_dropdown_list_json  = json.dumps(list(supervisor_dropdown_list) , cls=DjangoJSONEncoder)
            self.site_dropdown_list_json        = json.dumps(list(site_dropdown_list)       , cls=DjangoJSONEncoder)
            self.site_floor_dropdown_list_json  = json.dumps(list(site_floor_dropdown_list) , cls=DjangoJSONEncoder)
            self.site_type_dropdown_list_json   = json.dumps(list(site_type_dropdown_list)  , cls=DjangoJSONEncoder)

        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: EmpGridPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return None

        self.req_success = True
        return None

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)

            context["req_success"]                      = self.req_success
            context["err_msg"]                          = self.err_msg

            context["client_is_admin"]                  = self.client_is_admin

            context["emp_entry_columns_json"]           = self.emp_entry_columns_json
            context["emp_entries_json"]                 = self.emp_entries_json
            context["supervisor_dropdown_list_json"]    = self.supervisor_dropdown_list_json
            context["site_dropdown_list_json"]          = self.site_dropdown_list_json
            context["site_floor_dropdown_list_json"]    = self.site_floor_dropdown_list_json
            context["site_type_dropdown_list_json"]     = self.site_type_dropdown_list_json
            return context
        except Exception as e:
            self.req_success                            = False
            self.err_msg                                = "Exception: get_context_data(): {}".format(e)
            print(self.err_msg)

            context                                     = super().get_context_data(**kwargs)
            context["req_success"]                      = self.req_success
            context["err_msg"]                          = self.err_msg

            context["client_is_admin"]                  = False

            context["emp_entry_columns_json"]           = None
            context["emp_entries_json"]                 = None
            context["supervisor_dropdown_list_json"]    = None
            context["site_dropdown_list_json"]          = None
            context["site_floor_dropdown_list_json"]    = None
            context["site_type_dropdown_list_json"]     = None
            return context


## @TODO For front org chart view, the following. Move this chunk of code up before EmpGridPageView()
def GetClientWUPermissions(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: OrgChartPortal: GetClientWUPermissions(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetClientWUPermissions():\n\nUNAUTHENTICATE USER!",
        })

    ## Get the data
    try:
        wu_permissions_query = TblPermissionsWorkUnit.objects.using('OrgChartRead').filter(
                user_id__windows_username=remote_user
                ,user_id__active=True
            ).order_by('wu__wu')

        wu_permissions_list_json = list(wu_permissions_query.values('wu__wu', 'wu__wu_desc', 'wu__subdiv'))

        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": wu_permissions_list_json,
        })
    except Exception as e:
        err_msg = "Exception: OrgChartPortal: GetClientWUPermissions(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })


def GetClientTeammates(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: OrgChartPortal: GetClientTeammates(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetClientTeammates():\n\nUNAUTHENTICATE USER!",
        })

    ## Get the data
    try:
        wu_permissions_query = TblPermissionsWorkUnit.objects.using('OrgChartRead').filter(
                user_id__windows_username=remote_user
                ,user_id__active=True
            ).order_by('wu__wu')

        wu_permissions_list_json = wu_permissions_query.values('wu__wu')

        teammates_query = TblPermissionsWorkUnit.objects.using('OrgChartRead').filter(
                wu__wu__in=wu_permissions_list_json
                ,user_id__active=True
            ).order_by('pms__pms')

        teammates_list_json = list(teammates_query.values('pms__pms').annotate(pms__first_name=Min('pms__first_name'), pms__last_name=Min('pms__last_name')))

        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": teammates_list_json,
        })
    except Exception as e:
        err_msg = "Exception: OrgChartPortal: GetClientTeammates(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })


def GetEmpGridStats(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: OrgChartPortal: GetEmpGridStats(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetEmpGridStats():\n\nUNAUTHENTICATE USER!",
        })

    ## Get the data
    try:
        # teammates_list_json = list(teammates_query.values('pms__pms').annotate(pms__first_name=Min('pms__first_name'), pms__last_name=Min('pms__last_name')))

        allowed_wu_list_obj = get_allowed_list_of_wu(remote_user)
        if allowed_wu_list_obj['success'] == False:
            raise ValueError(f"get_allowed_list_of_wu() failed: {allowed_wu_list_obj['err']}")
        else:
            allowed_wu_list = allowed_wu_list_obj['wu_list']

        client_orgchart_data = TblEmployees.objects.using('OrgChartRead').filter(
            wu__wu__in=allowed_wu_list,
        ).order_by('wu__wu')

        emp_grid_stats_list_json = list(client_orgchart_data.values('pms').annotate(pms__first_name=Min('first_name'), pms__last_name=Min('last_name')))














        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": emp_grid_stats_list_json,
        })
    except Exception as e:
        err_msg = "Exception: OrgChartPortal: GetEmpGridStats(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })


class OrgChartPageView(generic.ListView):
    template_name = 'OrgChartPortal.template.orgchart.html'
    context_object_name = 'emp_entries'

    req_success = False
    err_msg = ""

    client_is_admin = False

    def get_queryset(self):
        ## Check for Active Admins
        is_active_admin = user_is_active_admin(self.request.user)
        if is_active_admin["isAdmin"] == True:
            self.client_is_admin = True
        else:
            self.client_is_admin = False

        ## Get the core data
        try:
            if self.client_is_admin == False:
                return None
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: OrgChartPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return None

        self.req_success = True
        return None

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


def GetEmpCsv(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: OrgChartPortal: GetEmpCsv(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetEmpCsv():\n\nUNAUTHENTICATE USER!",
        })

    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetEmpCsv():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    ## Get the data
    try:
        active_lv_list = ['B', 'C', 'K', 'M', 'N', 'Q', 'R', 'S']
        root_pms = json_blob['root_pms']

        ## Check for Active Admins
        is_admin = user_is_active_admin(remote_user)["isAdmin"]

        emp_data = TblEmployees.objects.using('OrgChartRead').exclude(
            Q(supervisor_pms__isnull=True) | Q(supervisor_pms__exact='')
            ,~Q(pms__exact=root_pms) # our very top root_pms will have a null supervisor_pms, so this condition is to include the top root_pms despite the first exclude condition
        ).filter(
            lv__in=active_lv_list
        ).order_by(
            'supervisor_pms'
        )

        flat_all_row_dict = emp_data.values( # Returns a query set that returns dicts. MUCH faster than going though emp_data in a for loop (53 secs down to 350ms).
            "pms"
            ,"last_name"
            ,"first_name"
            ,"office_title"
            ,"civil_title"
            ,"wu__wu_desc"
            ,"supervisor_pms"
        )


        # Add allowed WU filter to queryset since client is not admin
        if not is_admin:
            #raise ValueError(f"'{remote_user}' is not admin. Only admins can access the GetEmpCsv() api")
            allowed_wu_list_obj = get_allowed_list_of_wu(remote_user)
            if allowed_wu_list_obj['success'] == False:
                raise ValueError(f"get_allowed_list_of_wu() failed: {allowed_wu_list_obj['err']}")
            else:
                allowed_wu_list = allowed_wu_list_obj['wu_list']

            emp_data = emp_data.filter(
                Q(wu__in=allowed_wu_list)
            )

        # If admin, flat_allowed_row_dict will be the same as flat_all_row_dict, else len(flat_allowed_row_dict) < len(flat_all_row_dict)
        flat_allowed_row_dict = emp_data.values(
            "pms"
            ,"last_name"
            ,"first_name"
            ,"office_title"
            ,"civil_title"
            ,"wu__wu_desc"
            ,"supervisor_pms"
        )


        ## Build a dict of emp pms and a dict of its emp info
        ##  {
        ##      "1234566":
        ##          {
        ##              "pms":              "1234567"
        ##              "last_name":        "john"
        ##              "first_name":       "doe"
        ##              "supervisor_pms":   "7654321"
        ##          }
        ##      ,"7654321": {...}
        ##      .
        ##      .
        ##      .
        ##  }
        flat_all_processed_dict = {}
        for each in flat_all_row_dict:
            each_emp_dict = {}

            each_emp_dict[f"pms"]                   = f"{each['pms']}"              .strip() if each['pms']             is not None else None
            each_emp_dict[f"last_name"]             = f"{each['last_name']}"        .strip() if each['last_name']       is not None else None
            each_emp_dict[f"first_name"]            = f"{each['first_name']}"       .strip() if each['first_name']      is not None else None
            each_emp_dict[f"office_title"]          = f"{each['office_title']}"     .strip() if each['office_title']    is not None else None
            each_emp_dict[f"civil_title"]           = f"{each['civil_title']}"      .strip() if each['civil_title']     is not None else None
            each_emp_dict[f"wu_desc"]               = f"{each['wu__wu_desc']}"      .strip() if each['wu__wu_desc']     is not None else None
            each_emp_dict[f"supervisor_pms"]        = f"{each['supervisor_pms']}"   .strip() if each['supervisor_pms']  is not None else None
            each_emp_dict["is_needed_to_hit_root"]  = False

            flat_all_processed_dict[f"{each['pms']}".strip()] = each_emp_dict

        flat_allowed_processed_dict = {}
        for each in flat_allowed_row_dict:
            each_emp_dict = {}

            each_emp_dict[f"pms"]                   = f"{each['pms']}"              .strip() if each['pms']             is not None else None
            each_emp_dict[f"last_name"]             = f"{each['last_name']}"        .strip() if each['last_name']       is not None else None
            each_emp_dict[f"first_name"]            = f"{each['first_name']}"       .strip() if each['first_name']      is not None else None
            each_emp_dict[f"office_title"]          = f"{each['office_title']}"     .strip() if each['office_title']    is not None else None
            each_emp_dict[f"civil_title"]           = f"{each['civil_title']}"      .strip() if each['civil_title']     is not None else None
            each_emp_dict[f"wu_desc"]               = f"{each['wu__wu_desc']}"      .strip() if each['wu__wu_desc']     is not None else None
            each_emp_dict[f"supervisor_pms"]        = f"{each['supervisor_pms']}"   .strip() if each['supervisor_pms']  is not None else None

            flat_allowed_processed_dict[f"{each['pms']}".strip()] = each_emp_dict


        ## Only marks and add the nodes between leaf and root, including root. This does not mark and add the leaf nodes themself!
        def TraverseToRootAndMark(pms, nodes_away_from_leaf):
            ## pms is root_pms, so lineage is reachable to root_pms, return true
            if pms == root_pms:
                return True

            ## pms is a root that's not root_pms, so lineage is not reachable to root_pms, return false
            if pms == '' or pms is None:
                return False

            ## pms is not a root, check its parent
            try:
                parent_pms = flat_all_processed_dict[pms]['supervisor_pms']
            except KeyError:
                parent_pms = None

            ## If can reach root, mark the given parent pms as needed
            can_reach_root = TraverseToRootAndMark( pms=parent_pms, nodes_away_from_leaf=nodes_away_from_leaf+1 )
            if can_reach_root:
                flat_all_processed_dict[parent_pms]["is_needed_to_hit_root"] = True
                ## nodes_away_from_leaf == 0 means that the caller is a leaf node, and should mark the calling pms as needed.
                ## This is needed because the above line of code only mark a parent as needed, not the caller, so that means the caller will be miseed in the marking process
                if nodes_away_from_leaf == 0:
                    flat_all_processed_dict[pms]["is_needed_to_hit_root"] = True
            return can_reach_root


        ## For each node in the allowed dataset, mark its path of nodes needed to reach to the root as "Needed".
        for emp_pms in flat_allowed_processed_dict:
            emp = flat_allowed_processed_dict[emp_pms]
            TraverseToRootAndMark( pms=emp['pms'], nodes_away_from_leaf=0 )


        allowed_and_needed_nodes_dict = {}
        for key, value in flat_all_processed_dict.items():
            if value["is_needed_to_hit_root"] == True:
                allowed_and_needed_nodes_dict[key] = value


        if len(allowed_and_needed_nodes_dict) == 0:
            if not is_admin:
                raise ValueError(f"Found no orgchart data with the following client permission(s): {allowed_wu_list}")
            else:
                raise ValueError(f"Found no orgchart data despite client being an admin")


        import csv
        from io import StringIO
        dummy_in_mem_file = StringIO()

        ## Create the csv
        writer = csv.writer(dummy_in_mem_file)
        writer.writerow(["pms", "sup_pms", "last_name", "first_name", "office_title", "civil_title", "wu_desc"]) # For reference to what to name your id and parent id column: https://github.com/bumbeishvili/org-chart/issues/88
        # writer.writerow(["last_name", "first_name", "id", "parentId"])

        for each in allowed_and_needed_nodes_dict:
            try:
                ## In the case that root_pms is not the actual top root of the entire org tree, but it's a middle node somewhere, we need to set that emp's sup_pms to empty string
                if allowed_and_needed_nodes_dict[each]['pms'] == root_pms:
                    sup_pms = ""
                else:
                    sup_pms = allowed_and_needed_nodes_dict[each]['supervisor_pms']
            except Exception as e:
                raise e

            eachrow = [
                allowed_and_needed_nodes_dict[each]['pms']
                ,sup_pms
                ,allowed_and_needed_nodes_dict[each]['last_name']
                ,allowed_and_needed_nodes_dict[each]['first_name']
                ,allowed_and_needed_nodes_dict[each]['office_title']
                ,allowed_and_needed_nodes_dict[each]['civil_title']
                ,allowed_and_needed_nodes_dict[each]['wu_desc']
            ]
            writer.writerow(eachrow)


        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": dummy_in_mem_file.getvalue(),
        })
    except Exception as e:
        err_msg = "Exception: OrgChartPortal: GetEmpCsv(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })


## @TODO: Dont have a hard coded commisioner pms, serach for DOT commisioner office title, and active for that person
def GetCommissionerPMS(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: OrgChartPortal: GetCommissionerPMS(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetCommissionerPMS():\n\nUNAUTHENTICATE USER!",
        })


    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetCommissionerPMS():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    ## Get the data
    try:
        # ## Check for Active Admins
        # is_admin = user_is_active_admin(remote_user)["isAdmin"]
        # if not is_admin:
        #     raise ValueError(f"'{remote_user}' is not admin. Only admins can access the GetCommissionerPMS() api")


        from WebAppsMain.secret_settings import OrgChartRootPMS

        emp_data = TblEmployees.objects.using('OrgChartRead').filter(
            pms__exact=f'{OrgChartRootPMS}',
        ).first()

        pms = emp_data.pms

        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": pms,
        })
    except Exception as e:
        err_msg = "Exception: OrgChartPortal: GetCommissionerPMS(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })

