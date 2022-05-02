from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import generic
from django.http import HttpResponse, JsonResponse
from .models import *
from django.db.models import Min, Max, Q, F, Value, Case, When
from django.db.models.functions import Concat
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError
from django.utils import timezone
from datetime import timedelta
from dateutil import tz


# Create your views here.


## Check if remote user is admin and is active
def user_is_active_admin(username=None):
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
        return {
            "isAdmin": None,
            "err": 'Exception: user_is_active_admin(): {}'.format(e),
        }


class HomePageView(TemplateView):
    template_name   = 'OrgChartPortal.template.home.html'
    get_success     = True
    get_error       = None
    client_is_admin = None

    def get_context_data(self, **kwargs):
        try:
            ## Call the base implementation first to get a context
            context = super().get_context_data(**kwargs)
            self.client_is_admin = user_is_active_admin(self.request.user)["isAdmin"]
            context["client_is_admin"]  = self.client_is_admin
            context["get_success"]      = self.get_success
            context["get_error"]        = self.get_error
            return context
        except Exception as e:
            context["client_is_admin"]  = False
            context["get_success"]      = False
            context["get_error"]        = None
            return context


class AboutPageView(TemplateView):
    template_name   = 'OrgChartPortal.template.about.html'
    get_success     = True
    get_error       = None
    client_is_admin = None

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context["get_success"]      = self.get_success
            context["get_error"]        = self.get_error
            context["client_is_admin"]  = self.client_is_admin
            return context
        except Exception as e:
            context["get_success"]      = False
            context["get_error"]        = None
            context["client_is_admin"]  = None
            return context


class ContactPageView(TemplateView):
    template_name   = 'OrgChartPortal.template.contact.html'
    get_success     = True
    get_error       = None
    client_is_admin = None

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context["get_success"]      = self.get_success
            context["get_error"]        = self.get_error
            context["client_is_admin"]  = self.client_is_admin
            return context
        except Exception as e:
            context["get_success"]      = False
            context["get_error"]        = None
            context["client_is_admin"]  = None
            return context


def get_allowed_list_of_wu(username=None):
    try:
        wu_query = TblPermissionsWorkUnit.objects.using('OrgChartRead').filter(
            user_id__windows_username=username
            ,user_id__active=True
            ,is_active=True
        ).order_by('wu__wu')

        if wu_query.count() > 0:
            return [each.wu.wu for each in wu_query]
        raise ValueError(f"Cannot find any WU permissions for '{username}'")
    except Exception as e:
        raise ValueError(f"get_allowed_list_of_wu(): {e}")


def get_active_lv_list():
    return ['B', 'C', 'K', 'M', 'N', 'Q', 'R', 'S']


def get_active_tblemployee_qryset(read_only=True):
    """
        Return a queryset filtered to contain only records with active lv status plus a subset of 'L' leave status
        Lv status 'L' is usually Inactive, but when it is due to 'B10' Leave Status Reason (Look up from payroll history), that employee is actually Active
    """
    try:
        latest_pay_date     = TblPayrollHistory.objects.using('HRReportingRead').aggregate(Max('paydate'))['paydate__max']
        active_L_pms_qryset = TblPayrollHistory.objects.using('HRReportingRead').filter(
            lv__exact='L'
            ,lv_reason_code__exact='B10'
            ,paydate__exact=latest_pay_date
        )
        active_L_pms_list = [each['pms'] for each in list(active_L_pms_qryset.values('pms', 'lname', 'fname'))]

        if read_only:
            return TblEmployees.objects.using('OrgChartRead').filter(
                Q( lv__in=get_active_lv_list() )
                | Q( pms__in=active_L_pms_list )
            )
        else:
            return TblEmployees.objects.using('OrgChartWrite').filter(
                Q( lv__in=get_active_lv_list() )
                | Q( pms__in=active_L_pms_list )
            )
    except Exception as e:
        raise ValueError(f"get_active_tblemployee_qryset(): {e}")


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
        ,read_only = True
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
                ,custom_annotate_fct = annotate_fct
                ,read_only = True
                ...
            )
    '''

    qryset = get_active_tblemployee_qryset(read_only=read_only)

    if custom_annotate_fct is not None:
        qryset = custom_annotate_fct(qryset)

    ## To speed up the query, need to specify only the columns that is needed, so that django do a one-time query of the entire related dataset.
    return qryset.values(*fields_list)

'''
Checks if client is admin, and then return a queryset that filters for employees that the client has permissions to.
@username is required, rest of the argument is optional
'''
def get_active_permitted_emp_qryset(username=None, fields_list=None, read_only=True, custom_annotate_fct=None):
    try:
        if username is None:
            raise ValueError(f"@username cannot be None, must provide the client's username")

        client_is_admin = user_is_active_admin(username)['isAdmin']
        emp_data = get_active_emp_qryset(
            fields_list=fields_list
            ,custom_annotate_fct=custom_annotate_fct
            ,read_only=read_only
        )

        if client_is_admin:
            return emp_data
        else:
            allowed_wu_list = get_allowed_list_of_wu(username)

            emp_data = emp_data.filter(
                wu__wu__in=allowed_wu_list,
            )

            return emp_data

        return None
    except Exception as e:
        raise ValueError(f"get_active_permitted_emp_qryset(): {e}")


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
    * Returns True if new data is saved successfully.
    * Returns False if new data is the same as old data, presenting no change.
    * Raise the error if any exception is present.
'''
class EmpUpdateAndTrack:
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

        ## This list is the valid options for [ColumnName] in tblChanges
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

            ## timezone.now() is timezone awared, so when entered into the sql server, it will be stored as a UTC time. (Returns an aware or naive datetime.datetime, depending on settings.USE_TZ.)
            updated_on = timezone.now()
            if updated_on is None:
                raise ValueError(f"updated_on cannot be None.")
            if timezone.is_naive(updated_on):
                raise ValueError(f"updated_on cannot be a naive datetime object: '{updated_on}'")
            if timezone.is_aware(updated_on) and updated_on.tzname() not in ['UTC', 'Coordinated Universal Time']:
                raise ValueError(f"updated_on must be an aware datetime object in UTC timezone. updated_on's value: '{updated_on}' and timezone: '{updated_on.tzname()}'")

            if self.column_name not in self.valid_column_names:
                raise ValueError(f"{self.column_name} is not a valid column name.")


            ## Find the target employee row
            try:
                employee_row = get_active_tblemployee_qryset(read_only=False).get(pms__exact=self.updated_to_pms)
            except ObjectDoesNotExist as e:
                raise ValueError(f"The PMS '{self.updated_to_pms}' is either inactive or doesn't exists")


            ## Implementation of specific column updates
            additional_operation = None
            if self.column_name == 'SupervisorPMS':
                try:
                    new_supervisor_obj = get_active_tblemployee_qryset(read_only=False)
                    new_supervisor_obj = new_supervisor_obj.get(pms__exact=self.new_value)
                except ObjectDoesNotExist as e:
                    raise ValueError(f"The Supervisor PMS '{self.new_value}' is either inactive or doesn't exist")

                ## Data validation
                if employee_row.supervisor_pms_id is not None and employee_row.supervisor_pms_id.strip() != '' and employee_row.supervisor_pms.pms == new_supervisor_obj.pms:
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
                    employee_row.actual_site_id         = new_site_obj
                    employee_row.actual_floor_id        = None
                    employee_row.actual_site_type_id    = None

                    ## Additional operation to be perform in the transaction. Record the changes to Site Floor Id and Site Type Id.
                    def additional_operation_tbl_changes():
                        change_record_site_floor_row = TblChanges(
                            updated_on      = updated_on
                            ,updated_by_pms = self.updated_by_pms
                            ,updated_to_pms = self.updated_to_pms
                            ,new_value      = None
                            ,column_name    = 'ActualFloorId'
                        )

                        change_record_site_type_row = TblChanges(
                            updated_on      = updated_on
                            ,updated_by_pms = self.updated_by_pms
                            ,updated_to_pms = self.updated_to_pms
                            ,new_value      = None
                            ,column_name    = 'ActualSiteTypeId'
                        )

                        change_record_site_floor_row.save(using='OrgChartWrite')
                        change_record_site_type_row.save(using='OrgChartWrite')

                    additional_operation = additional_operation_tbl_changes

            elif self.column_name == 'ActualFloorId':
                try:
                    new_floor_obj = TblDOTSiteFloors.objects.using('OrgChartWrite').get(floor_id__exact=self.new_value)
                except ObjectDoesNotExist as e:
                    raise ValueError(f"The Floor Id '{self.new_value}' doesn't exist")

                ## Data validation
                if employee_row.actual_floor_id is not None and employee_row.actual_floor_id.floor_id == new_floor_obj.floor_id:
                    ## Return False because new value is same as old value
                    return False
                elif employee_row.actual_site_id is None:
                    raise ValueError(f"Cannot set the floor for employee when their site is null")
                elif employee_row.actual_site_id.site_id != new_floor_obj.site_id.site_id:
                    ## Floor_Id must be associated with employee's current Site_Id
                    raise ValueError(f"Floor ({new_floor_obj.floor}-{self.new_value}) is not a valid floor for ({employee_row.actual_site_id.site}-{employee_row.actual_site_id.site_id})")
                else:
                    employee_row.actual_floor_id = new_floor_obj

                    valid_site_types_obj = TblDOTSiteFloorSiteTypes.objects.using('OrgChartWrite').filter(
                        floor_id__exact=self.new_value
                    )
                    if valid_site_types_obj.count() == 1:
                        site_type_id                = valid_site_types_obj[:1][0].site_type_id.site_type_id ## [:1] is the LIMIT 1 query. And then [0] gets the first object out of the queryset
                        only_site_type_for_floor    = TblDOTSiteTypes.objects.using('OrgChartWrite').get(site_type_id__exact=site_type_id)

                        if (
                            (employee_row.actual_site_type_id is None) # Existing is NULL, so replace it!
                            or (employee_row.actual_site_type_id is not None and employee_row.actual_site_type_id.site_type_id != only_site_type_for_floor.site_type_id)
                        ):
                            ## Only update the site type id if it's different than existing
                            employee_row.actual_site_type_id    = only_site_type_for_floor

                            ## Additional operation to be perform in the transaction. Record the changes to Site Floor Id and Site Type Id.
                            def additional_operation_tbl_changes():
                                change_record_site_type_row = TblChanges(
                                    updated_on      = updated_on
                                    ,updated_by_pms = self.updated_by_pms
                                    ,updated_to_pms = self.updated_to_pms
                                    ,new_value      = only_site_type_for_floor.site_type_id
                                    ,column_name    = 'ActualSiteTypeId'
                                )

                                change_record_site_type_row.save(using='OrgChartWrite')

                            additional_operation = additional_operation_tbl_changes

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

                    if additional_operation is not None:
                        additional_operation()

                    change_record_row = TblChanges(
                        updated_on      = updated_on
                        ,updated_by_pms = self.updated_by_pms
                        ,updated_to_pms = self.updated_to_pms
                        ,new_value      = self.new_value
                        ,column_name    = self.column_name
                    )

                    change_record_row.save(using='OrgChartWrite')
            except Exception as e:
                raise ValueError(f"While commiting the atomic transaction: {e}")

            return True
        except Exception as e:
            raise ValueError(f"Class EmpUpdateAndTrack: save(): {e}")


def UpdateEmployeeData(request):

    if request.method != "POST":
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"UpdateEmployeeData(): {request.method} HTTP request not supported",
            "post_data"     : None
        })

    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: UpdateEmployeeData(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : "UpdateEmployeeData():\n\nUNAUTHENTICATE USER!",
            "post_data"     : None,
        })

    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"UpdateEmployeeData():\n\nUnable to load request.body as a json object: {e}",
            "post_data"     : None
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
            'Supervisor'    : 'SupervisorPMS'
            ,'Office Title' : 'OfficeTitle'
            ,'Site'         : 'ActualSiteId'
            ,'Floor'        : 'ActualFloorId'
            ,'Site Type'    : 'ActualSiteTypeId'
        }

        if column_name not in list(valid_editable_column_names_mapping.keys()):
            raise ValueError(f"{column_name} is not an editable column")

        if new_value is None:
            raise ValueError(f"new_value for {column_name} cannot be None")
        elif new_value == '':
            raise ValueError(f"new_value for {column_name} cannot be empty text")
        elif type(new_value) is not str:
            raise ValueError(f"new_value for {column_name} is not {type('')} type, the current type is {type(new_value)}")

        # Check for permission to edit the target employee row
        is_admin = user_is_active_admin(remote_user)["isAdmin"]
        if not is_admin:
            allowed_wu_list = get_allowed_list_of_wu(remote_user)

            try:
                employee_row = get_active_tblemployee_qryset(read_only=False).get(pms__exact=to_pms)
            except ObjectDoesNotExist as e:
                raise ValueError(f"The PMS '{to_pms}' is either inactive or doesn't exists")
            if employee_row.wu.wu not in allowed_wu_list:
                raise ValueError(f"user doesn't not have permission to edit {employee_row.pms}'s record (Need permission to their WU)")


        ## Get the client's user obj from database
        try:
            remote_user_obj = TblUsers.objects.using('OrgChartWrite').get(windows_username__exact=remote_user)
        except ObjectDoesNotExist as e:
            raise ValueError(f"The client '{remote_user}' is not a user of the system")


        atomic_update = EmpUpdateAndTrack(
            updated_by_pms  = remote_user_obj.pms.pms
            ,updated_to_pms = to_pms
            ,new_value      = new_value
            ,column_name    = valid_editable_column_names_mapping[column_name]
        )
        if not atomic_update.save():
            raise ValueError(f"No change in data, no update needed.")

        return JsonResponse({
            "post_success"  : True,
            "post_msg"      : None,
            "post_data"     : None
        })

    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"UpdateEmployeeData():\n\nError: {e}",
            # "post_msg"      : f"UpdateEmployeeData():\n\nError: {e}. The exception type is: {e.__class__.__name__}",
            "post_data"     : None
        })


def GetClientWUPermissions(request):
    """
        Return a list of WU permission related to the requesting client.
        If client is admin, will return a none null post_msg and a true post_success.
    """
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
        is_admin = user_is_active_admin(remote_user)["isAdmin"]
        if is_admin:
            return JsonResponse({
                "post_success": True,
                "post_msg": 'User is Admin',
                "post_data": {
                    "wu_permissions": None
                },
            })
        else:
            wu_permissions_query = TblPermissionsWorkUnit.objects.using('OrgChartRead').filter(
                    user_id__windows_username=remote_user
                    ,user_id__active=True
                    ,is_active=True
                ).order_by('wu__wu')

            wu_permissions_list_json = list(wu_permissions_query.values('wu__wu', 'wu__wu_desc', 'wu__subdiv'))

            return JsonResponse({
                "post_success": True,
                "post_msg": None,
                "post_data": {
                    "wu_permissions": wu_permissions_list_json
                },
            })


    except Exception as e:
        get_error = "Exception: OrgChartPortal: GetClientWUPermissions(): {}".format(e)
        return JsonResponse({
            "post_success": False,
            "post_msg": get_error
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
        is_admin = user_is_active_admin(remote_user)["isAdmin"]
        if is_admin:
            return JsonResponse({
                "post_success": True,
                "post_msg": 'User is Admin',
                "post_data": {
                    "teammates": None
                },
            })
        else:
            wu_permissions_query = TblPermissionsWorkUnit.objects.using('OrgChartRead').filter(
                    user_id__windows_username=remote_user
                    ,user_id__active=True
                ).order_by('wu__wu')

            wu_permissions_list = wu_permissions_query.values('wu__wu')

            teammates_query = TblPermissionsWorkUnit.objects.using('OrgChartRead').filter(
                wu__wu__in=wu_permissions_list
                ,user_id__active=True
                ,is_active=True
            ).order_by('user_id__pms__pms')

            teammates_list_json = list(teammates_query.values('user_id__pms__pms').annotate(user_id__pms__first_name=Min('user_id__pms__first_name'), user_id__pms__last_name=Min('user_id__pms__last_name')))

            return JsonResponse({
                "post_success": True,
                "post_msg": None,
                "post_data": {
                    "teammates": teammates_list_json
                },
            })
    except Exception as e:
        get_error = "Exception: OrgChartPortal: GetClientTeammates(): {}".format(e)
        return JsonResponse({
            "post_success": False,
            "post_msg": get_error
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
        def annotate_emp_full_name(qryset):
            return qryset.annotate(
                annotated__full_name=Concat( F('last_name'), Value(', '), F('first_name') )
                ,annotated__supervisor_full_name=Concat( F('supervisor_pms__last_name'), Value(', '), F('supervisor_pms__first_name') )
            )

        fields_list = [
            'pms'
            ,'wu__wu'
            ,'annotated__full_name'
            ,'supervisor_pms__pms'
            ,'supervisor_pms__lv'
            ,'annotated__supervisor_full_name'
            ,'office_title'
            ,'actual_site_id__site_id'
            ,'actual_floor_id__floor_id'
            ,'actual_floor_id__site_id'
            ,'actual_site_type_id__site_type_id'
        ]
        active_permitted_emp = get_active_permitted_emp_qryset(username=remote_user, fields_list=fields_list, read_only=True, custom_annotate_fct=annotate_emp_full_name)
        active_permitted_emp = active_permitted_emp.order_by('wu__wu')

        is_admin = user_is_active_admin(remote_user)["isAdmin"]

        def get_supervisor_completed():
            try:
                total_count = active_permitted_emp.count()

                sup_completed_count = active_permitted_emp.filter(
                    Q(supervisor_pms__pms__isnull=False)    # not null
                    & ~Q(supervisor_pms__pms__exact="")     # not empty
                ).count()

                sup_completed_percentage = float(sup_completed_count)/float(total_count) * 100

                return sup_completed_percentage
            except Exception as e:
                raise ValueError(f"get_supervisor_completed(): {e}")

        def get_office_title_completed():
            try:
                total_count = active_permitted_emp.count()

                office_title_completed_count = active_permitted_emp.filter(
                    Q(office_title__isnull=False)   # not null
                    & ~Q(office_title__exact="")    # not empty
                ).count()

                office_title_completed_percentage = float(office_title_completed_count)/float(total_count) * 100

                return office_title_completed_percentage
            except Exception as e:
                raise ValueError(f"get_office_title_completed(): {e}")

        def get_latest_change():
            try:
                total_count = active_permitted_emp.count()
                # active_permitted_emp already check if client is admin. But if client is admin, the PMS list would be HUGE, so I am placing an check here to avoid computing the PMS list if client is admin.
                # If client is admin, just return the latest row of the entire tblChanges without filtering for a PMS list
                changes = TblChanges.objects.using('OrgChartRead')
                if not is_admin:
                    changes = changes.filter(
                        ## Provide an inner query instead of a python list, to bypass the 1000 items for the IN clause limit
                        updated_to_pms__in=active_permitted_emp.values('pms')
                    )

                if changes.count() == 0:
                    return None
                else:
                    changes = changes.order_by('-updated_on')[:1] ## Offset 0, Limit 1 in SQL

                latest_change = list(changes.values(
                    'id'
                    ,'updated_on'
                    ,'updated_by_pms'
                    ,'updated_to_pms'
                    ,'new_value'
                    ,'column_name'
                ))[0]
                latest_change['updated_on_est'] = latest_change['updated_on'].astimezone(tz.gettz('America/New_York'))
                return latest_change
            except Exception as e:
                raise ValueError(f"get_latest_change(): {e}")

        def get_list_last_updated_on_est():
            try:
                total_count = active_permitted_emp.count()
                latest_change = get_latest_change()
                if latest_change is None:
                    return None
                else:
                    return get_latest_change()['updated_on_est'].strftime('%m/%d/%Y %I:%M:%S %p')
            except Exception as e:
                raise ValueError(f"get_list_last_updated_on_est(): {e}")

        def get_list_last_updated_by():
            try:
                total_count = active_permitted_emp.count()
                latest_change = get_latest_change()
                if latest_change is None:
                    return None
                else:
                    ## latest_updated_by_pms could now be an inactive employee, or be an employee with a WU that the client doesn't have permission to access.
                    ## Since it's just a windows username look up, we forgo the usual WU permission check.
                    lastest_updated_by_pms  = get_latest_change()['updated_by_pms']
                    updated_by_emp          = TblEmployees.objects.using('OrgChartRead').annotate(
                        annotated__full_name=Concat( F('last_name'), Value(', '), F('first_name') )
                    ).get(pms__exact=lastest_updated_by_pms)
                    return updated_by_emp.annotated__full_name
            except Exception as e:
                raise ValueError(f"get_list_last_updated_by(): Trying to search for lastest_updated_by_pms '{lastest_updated_by_pms}' but encountered: {e}")

        def get_inactive_supervisors():
            try:
                total_count = active_permitted_emp.count()
                inactive_sup = active_permitted_emp.filter(
                    Q(supervisor_pms__pms__isnull=False)
                    & ~Q(supervisor_pms__lv__in=get_active_lv_list())
                )

                return [
                    {
                        'Employee'              : each['annotated__full_name']
                        ,'WU'                   : each['wu__wu']
                        ,'Inactive_Supervisor'  : each['annotated__supervisor_full_name']
                    }
                    for each
                    in inactive_sup
                ]
            except Exception as e:
                raise ValueError(f"get_inactive_supervisors(): {e}")

        def get_empty_or_invalid_floor_combo_list():
            try:
                total_count = active_permitted_emp.count()
                invalid_site_and_floor = active_permitted_emp.filter(
                    Q(actual_floor_id__floor_id__isnull=True)
                    | ~Q(actual_floor_id__site_id=F('actual_site_id__site_id'))
                )

                return [
                    {
                        'Employee'  : each['annotated__full_name']
                        ,'WU'       : each['wu__wu']
                    }
                    for each
                    in invalid_site_and_floor
                ]
            except Exception as e:
                raise ValueError(f"get_empty_or_invalid_floor_combo_list(): {e}")

        def get_empty_or_invalid_site_type_combo_list():
            try:
                total_count = active_permitted_emp.count()
                valid_combo = TblDOTSiteFloorSiteTypes.objects.using('OrgChartRead').values(
                    'site_type_id'
                    ,'floor_id__floor_id'
                    ,'floor_id__site_id'
                )
                valid_combo = list(valid_combo)

                invalid_site_and_floor_and_site_type = [
                    {
                        'Employee'                              : each['annotated__full_name']
                        ,'WU'                                   : each['wu__wu']
                        ,'actual_site_id__site_id'              : each['actual_site_id__site_id']
                        ,'actual_floor_id__floor_id'            : each['actual_floor_id__floor_id']
                        ,'actual_site_type_id__site_type_id'    : each['actual_site_type_id__site_type_id']
                    }
                    for each
                    in active_permitted_emp
                ]

                def is_valid_combo(valid_combo=None, row=None):
                    actual_site_type_id = row['actual_site_type_id__site_type_id']
                    actual_floor_id     = row['actual_floor_id__floor_id']
                    actual_site_id      = row['actual_site_id__site_id']

                    found = [
                        each
                        for each
                        in valid_combo
                        if (
                            each['site_type_id']            == actual_site_type_id
                            and each['floor_id__floor_id']  == actual_floor_id
                            and each['floor_id__site_id']   == actual_site_id
                        )
                    ]

                    if len(found) > 1:
                        raise ValueError(f"Found more than one valid combo for Site Type. Should only find one match, not {len(found)} matches: {found}")
                    elif len(found) == 1:
                        return True
                    else:
                        return False


                for each in invalid_site_and_floor_and_site_type:
                    if is_valid_combo(valid_combo=valid_combo, row=each):
                        each['valid_site_type_combo'] = True
                    else:
                        each['valid_site_type_combo'] = False

                invalid_site_and_floor_and_site_type = [
                    {
                        'Employee'  : each['Employee']
                        ,'WU'       : each['WU']
                    }
                    for each
                    in invalid_site_and_floor_and_site_type
                    if each['valid_site_type_combo'] == False
                ]

                return list(invalid_site_and_floor_and_site_type)
            except Exception as e:
                raise ValueError(f"get_empty_or_invalid_site_type_combo_list(): {e}")

        emp_grid_stats_json = {
            'supervisor_completed'                      : get_supervisor_completed()
            ,'office_title_completed'                   : get_office_title_completed()
            ,'list_last_updated_on_est'                 : get_list_last_updated_on_est()
            ,'list_last_updated_by'                     : get_list_last_updated_by()
            ,'inactive_supervisor_list'                 : get_inactive_supervisors()
            ,'empty_or_invalid_floor_combo_list'        : get_empty_or_invalid_floor_combo_list()
            ,'empty_or_invalid_site_type_combo_list'    : get_empty_or_invalid_site_type_combo_list()
        }


        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": emp_grid_stats_json,
        })
    except Exception as e:
        get_error = "Exception: OrgChartPortal: GetEmpGridStats(): {}".format(e)
        return JsonResponse({
            "post_success": False,
            "post_msg": get_error
        })


def EmpGridGetCsvExport(request):
    if request.method != "POST":
        return JsonResponse({
            "post_success": False,
            "post_msg": f"{request.method} HTTP request not supported",
        })


    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: EmpGridGetCsvExport(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "EmpGridGetCsvExport():\n\nUNAUTHENTICATE USER!",
            "post_data": None,
        })


    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Exception: OrgChartPortal: EmpGridGetCsvExport():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    try:
        import csv
        from io import StringIO
        dummy_in_mem_file = StringIO()

        # some_post_param   = json_blob['some_post_param']

        is_admin = user_is_active_admin(remote_user)["isAdmin"]

        fields_list = [
            'pms'
            ,'last_name'
            ,'first_name'
            ,'lv'
            ,'wu__wu'
            ,'civil_title'
            ,'office_title'
            ,'supervisor_pms__pms'
            ,'annotated__supervisor_full_name'
            ,'actual_site_id__site'
            ,'actual_floor_id__floor'
            ,'actual_site_type_id__site_type'
        ]

        def annotate_emp_full_name(qryset):
            return qryset.annotate(
                annotated__full_name=Concat( F('last_name'), Value(', '), F('first_name') )
                ,annotated__supervisor_full_name=Concat( F('supervisor_pms__last_name'), Value(', '), F('supervisor_pms__first_name') )
            )

        active_permitted_emp = get_active_permitted_emp_qryset(username=remote_user, fields_list=fields_list, read_only=True, custom_annotate_fct=annotate_emp_full_name)
        active_permitted_emp = active_permitted_emp.order_by('wu__wu')


        ## Create the csv
        writer = csv.writer(dummy_in_mem_file)
        writer.writerow(['PMS', 'Last Name', 'First Name', 'Lv', 'WU', 'Title', 'Office Title', 'Supervisor PMS', 'Supervisor', 'Site', 'Floor', 'Site Type'])

        for each in active_permitted_emp:
            eachrow = [
                each['pms']
                ,each['last_name']
                ,each['first_name']
                ,each['lv']
                ,each['wu__wu']
                ,each['civil_title']
                ,each['office_title']
                ,each['supervisor_pms__pms']
                ,each['annotated__supervisor_full_name']
                ,each['actual_site_id__site']
                ,each['actual_floor_id__floor']
                ,each['actual_site_type_id__site_type']
            ]
            writer.writerow(eachrow)

        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_csv_bytes": dummy_in_mem_file.getvalue(),
        })
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": f"Exception: OrgChartPortal: EmpGridGetCsvExport():\n\nError: {e}",
            # "post_msg": "Exception: OrgChartPortal: EmpGridGetCsvExport():\n\nError: {}. The exception type is:{}".format(e,  e.__class__.__name__),
        })


class EmpGridPageView(generic.ListView):
    template_name                   = 'OrgChartPortal.template.empgrid.html'

    get_success                     = False
    get_error                       = ""
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
                {'headerName': 'PMS'            , 'field': 'pms'                                  , 'suppressMovable': True , 'lockPinned': True , 'cellClass': 'left-pinned' , 'pinned': 'left' , 'width': 80}
                ,{'headerName': 'Last Name'     , 'field': 'last_name'                            , 'suppressMovable': True , 'lockPinned': True , 'cellClass': 'left-pinned' , 'pinned': 'left' , 'width': 110}
                ,{'headerName': 'First Name'    , 'field': 'first_name'                           , 'suppressMovable': True , 'lockPinned': True , 'cellClass': 'left-pinned' , 'pinned': 'left' , 'width': 110}
                ,{'headerName': 'Lv'            , 'field': 'lv'                                   , 'suppressMovable': True , 'lockPinned': True , 'cellClass': 'left-pinned' , 'pinned': 'left' , 'width': 65}
                ,{'headerName': 'WU'            , 'field': 'wu__wu'                               , 'suppressMovable': True , 'lockPinned': True , 'cellClass': 'left-pinned' , 'pinned': 'left' , 'width': 75}
                ,{'headerName': 'Title'         , 'field': 'civil_title'                          , 'suppressMovable': True , 'lockPinned': True , 'cellClass': 'left-pinned' , 'pinned': 'left' , 'width': 230}
                ,{'headerName': 'Office Title'  , 'field': 'office_title'                         , 'suppressMovable': True , 'lockPinned': True}
                ,{'headerName': 'Supervisor'    , 'field': 'supervisor_pms__pms'                  , 'suppressMovable': True , 'lockPinned': True}
                ,{'headerName': 'Site'          , 'field': 'actual_site_id__site_id'              , 'suppressMovable': True , 'lockPinned': True}
                ,{'headerName': 'Floor'         , 'field': 'actual_floor_id__floor_id'            , 'suppressMovable': True , 'lockPinned': True}
                ,{'headerName': 'Site Type'     , 'field': 'actual_site_type_id__site_type_id'    , 'suppressMovable': True , 'lockPinned': True}
            ]

            fields_list = [each['field'] for each in ag_grid_col_def]

            emp_entries = get_active_permitted_emp_qryset(username=self.request.user, fields_list=fields_list, read_only=True, custom_annotate_fct=None)
            emp_entries = emp_entries.order_by('wu__wu', 'last_name')

            supervisor_dropdown_list = get_active_emp_qryset(
                fields_list=[
                    'pms'
                    ,'annotated__full_name'
                ]
                ,custom_annotate_fct=annotate_emp_full_name
                ,read_only = True
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

            self.emp_entry_columns_json         = json.dumps(list(ag_grid_col_def)          , cls=DjangoJSONEncoder)
            self.emp_entries_json               = json.dumps(list(emp_entries)              , cls=DjangoJSONEncoder)
            self.supervisor_dropdown_list_json  = json.dumps(list(supervisor_dropdown_list) , cls=DjangoJSONEncoder)
            self.site_dropdown_list_json        = json.dumps(list(site_dropdown_list)       , cls=DjangoJSONEncoder)
            self.site_floor_dropdown_list_json  = json.dumps(list(site_floor_dropdown_list) , cls=DjangoJSONEncoder)
            self.site_type_dropdown_list_json   = json.dumps(list(site_type_dropdown_list)  , cls=DjangoJSONEncoder)

        except Exception as e:
            self.get_success = False
            self.get_error = "Exception: EmpGridPageView(): get_queryset(): {}".format(e)
            return None

        self.get_success = True
        return None

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)

            context["get_success"]                      = self.get_success
            context["get_error"]                        = self.get_error
            context["client_is_admin"]                  = self.client_is_admin

            context["emp_entry_columns_json"]           = self.emp_entry_columns_json
            context["emp_entries_json"]                 = self.emp_entries_json
            context["supervisor_dropdown_list_json"]    = self.supervisor_dropdown_list_json
            context["site_dropdown_list_json"]          = self.site_dropdown_list_json
            context["site_floor_dropdown_list_json"]    = self.site_floor_dropdown_list_json
            context["site_type_dropdown_list_json"]     = self.site_type_dropdown_list_json
            return context
        except Exception as e:
            self.get_success                            = False
            self.get_error                                = "Exception: get_context_data(): {}".format(e)

            context                                     = super().get_context_data(**kwargs)
            context["get_success"]                      = self.get_success
            context["get_error"]                          = self.get_error

            context["client_is_admin"]                  = False

            context["emp_entry_columns_json"]           = None
            context["emp_entries_json"]                 = None
            context["supervisor_dropdown_list_json"]    = None
            context["site_dropdown_list_json"]          = None
            context["site_floor_dropdown_list_json"]    = None
            context["site_type_dropdown_list_json"]     = None
            return context


class OrgChartPageView(generic.ListView):
    template_name   = 'OrgChartPortal.template.orgchart.html'

    get_success     = True
    get_error       = ""
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
            self.get_success = False
            self.get_error = "Exception: OrgChartPageView(): get_queryset(): {}".format(e)
            return None

        self.get_success = True
        return None

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)

            context["get_success"]      = self.get_success
            context["get_error"]        = self.get_error
            context["client_is_admin"]  = self.client_is_admin

            return context
        except Exception as e:
            self.get_success = False
            self.get_error = "Exception: get_context_data(): {}".format(e)

            context = super().get_context_data(**kwargs)
            context["get_success"]      = self.get_success
            context["get_error"]        = self.get_error
            context["client_is_admin"]  = False

            return context


def OrgChartGetEmpCsv(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: OrgChartPortal: OrgChartGetEmpCsv(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: OrgChartGetEmpCsv():\n\nUNAUTHENTICATE USER!",
        })

    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: OrgChartGetEmpCsv():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    ## Get the data
    try:
        root_pms = json_blob['root_pms']

        ## Check for Active Admins
        is_admin = user_is_active_admin(remote_user)["isAdmin"]

        emp_data = TblEmployees.objects.using('OrgChartRead').exclude(
            Q(supervisor_pms__isnull=True) | Q(supervisor_pms__exact='')
            ,~Q(pms__exact=root_pms) # our very top root_pms will have a null supervisor_pms, so this condition is to include the top root_pms despite the first exclude condition
        ).filter(
            lv__in=get_active_lv_list()
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
            #raise ValueError(f"'{remote_user}' is not admin. Only admins can access the OrgChartGetEmpCsv() api")
            allowed_wu_list = get_allowed_list_of_wu(remote_user)

            emp_data = emp_data.filter(
                Q(wu__in=allowed_wu_list)
            )

        if emp_data.count() == 0:
            if not is_admin:
                raise ValueError(f"Found no orgchart data with the following client permission(s): {allowed_wu_list}")
            else:
                raise ValueError(f"Found no orgchart data despite client being an admin")

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
            raise ValueError(f"Found no orgchart relationship from root pms")


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
        get_error = "Exception: OrgChartPortal: OrgChartGetEmpCsv(): {}".format(e)
        return JsonResponse({
            "post_success": False,
            "post_msg": get_error
        })


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


        emp_data = TblEmployees.objects.using('OrgChartRead').filter(
            civil_title='Commissioner-DOT'
            ,lv__in=get_active_lv_list()
        )

        if emp_data.count() == 0:
            raise ValueError(f"Cannot find an active DOT Commissioner in the database")
        elif emp_data.count() > 1:
            raise ValueError(f"Found more than one active DOT Commissioners in the database (Found {emp_data.count()})")

        dot_commissioner = emp_data.first()

        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": dot_commissioner.pms,
        })
    except Exception as e:
        get_error = "Exception: OrgChartPortal: GetCommissionerPMS(): {}".format(e)
        return JsonResponse({
            "post_success": False,
            "post_msg": get_error
        })


class AdminPanelPageView(generic.ListView):
    template_name   = 'OrgChartPortal.template.adminpanel.html'

    get_success     = True
    get_error       = ""
    client_is_admin = False

    def get_queryset(self):
        # Check for Active Admins
        self.client_is_admin = user_is_active_admin(self.request.user)["isAdmin"]

        ## Get the core data
        try:
            if not self.client_is_admin:
                raise ValueError("'{}' is not an Admin, and is not authorized to see this page.".format(self.request.user))

        except Exception as e:
            self.get_success = False
            self.get_error = "Exception: AdminPanelPageView(): get_queryset(): {}".format(e)
            return None

        self.get_success = True
        return None

    def get_context_data(self, **kwargs):
        try:
            context                     = super().get_context_data(**kwargs)
            context["get_success"]      = self.get_success
            context["get_error"]        = self.get_error
            context["client_is_admin"]  = self.client_is_admin
            return context
        except Exception as e:
            self.get_success = False
            self.get_error = "Exception: AdminPanelPageView(): get_context_data(): {}".format(e)

            context                     = super().get_context_data(**kwargs)
            context["get_success"]      = self.get_success
            context["get_error"]          = self.get_error
            context["client_is_admin"]  = False
            return context


class ManageUsersPageView(generic.ListView):
    template_name           = 'OrgChartPortal.template.manageusers.html'

    get_success             = False
    get_error               = ""
    client_is_admin         = False

    ag_grid_col_def_json    = None
    users_data_json         = None

    def get_queryset(self):
        # Check for Active Admins
        self.client_is_admin = user_is_active_admin(self.request.user)["isAdmin"]

        ## Get the core data
        try:
            if self.client_is_admin:
                ag_grid_col_def = [ ## Need to format this way for AG Grid
                    {'headerName': 'PMS'                , 'field': 'pms'                , 'suppressMovable': True , 'lockPinned': True , 'cellClass': 'notEditableColorCode'}
                    ,{'headerName': 'Windows Username'  , 'field': 'windows_username'   , 'suppressMovable': True , 'lockPinned': True , 'cellClass': 'notEditableColorCode'}
                    ,{'headerName': 'Is Admin'          , 'field': 'is_admin'           , 'suppressMovable': True , 'lockPinned': True}
                    ,{'headerName': 'Active'            , 'field': 'active'             , 'suppressMovable': True , 'lockPinned': True}
                    ,{'headerName': 'Delete?'           , 'field': None                 , 'suppressMovable': True , 'lockPinned': True}
                ]
                fields_list = [ each['field'] for each in ag_grid_col_def if each['field'] is not None ]

                users_data = TblUsers.objects.using('OrgChartRead').all().order_by('windows_username').values(*fields_list)

                self.ag_grid_col_def_json = json.dumps(list(ag_grid_col_def), cls=DjangoJSONEncoder)
                self.users_data_json      = json.dumps(list(users_data)     , cls=DjangoJSONEncoder)
            else:
                raise ValueError("'{}' is not an Admin, and is not authorized to see this page.".format(self.request.user))

        except Exception as e:
            self.get_success    = False
            self.get_error        = "Exception: ManageUsersPageView(): get_queryset(): {}".format(e)
            return None

        self.get_success = True
        return None

    def get_context_data(self, **kwargs):
        try:
            context                         = super().get_context_data(**kwargs)
            context["get_success"]          = self.get_success
            context["get_error"]            = self.get_error
            context["client_is_admin"]      = self.client_is_admin
            context["ag_grid_col_def_json"] = self.ag_grid_col_def_json
            context["users_data_json"]      = self.users_data_json
            return context
        except Exception as e:
            self.get_success                = False
            self.get_error                  = f"Exception: ManageUsersPageView(): get_context_data(): {e}"

            context                         = super().get_context_data(**kwargs)
            context["get_success"]          = self.get_success
            context["get_error"]            = self.get_error
            context["client_is_admin"]      = False
            context["ag_grid_col_def_json"] = None
            context["users_data_json"]      = None
            return context


def AddUser(request):

    if request.method != "POST":
        return JsonResponse({
            "post_success": False,
            "post_msg": "{} HTTP request not supported".format(request.method),
        })


    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: AddUser(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "AddUser():\n\nUNAUTHENTICATE USER!",
            "post_data": None,
        })


    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "AddUser():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    try:
        windows_username    = json_blob['windows_username']
        pms                 = json_blob['pms']
        is_admin            = json_blob['is_admin']


        if not user_is_active_admin(remote_user)["isAdmin"]:
            raise ValueError("'{}' is not admin and does not have the permission to add a new user".format(remote_user))


        if windows_username is None:
            raise ValueError("windows_username cannot be null")
        elif windows_username == '':
            raise ValueError("windows_username cannot be empty string")
        elif ' ' in windows_username:
            raise ValueError("windows_username cannot contain whitespace")

        if pms is None:
            raise ValueError("pms cannot be null")
        elif pms == '':
            raise ValueError("pms cannot be empty string")
        elif len(pms) != 7 or not pms.isdigit():
            raise ValueError("pms is not a 7 digit number")

        if is_admin not in ['True', 'False']:
            raise ValueError(f"Unrecognized is_admin value '{is_admin}', must be either 'True' or 'False'")


        try:
            emp = TblEmployees.objects.using("OrgChartWrite").get(pms=pms)
        except ObjectDoesNotExist as e:
            raise ValueError(f"Cannot find an employee in TblEmployees with the pms '{pms}'")

        try:
            new_user = TblUsers(windows_username=windows_username, pms=emp, is_admin=is_admin)
            new_user.save(using='OrgChartWrite')
        except Exception as e:
            raise e

        return JsonResponse({
            "post_success"      : True,
            "post_msg"          : None,
            "windows_username"  : new_user.windows_username,
            "pms"               : new_user.pms.pms,
            "is_admin"          : new_user.is_admin,
        })
    except ObjectDoesNotExist as e:
        return JsonResponse({
            "post_success"      : False,
            "post_msg"          : f"OrgChartPortal: AddUser():\n\nError: {e}",
            "windows_username"  : new_user.windows_username
        })
    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"OrgChartPortal: AddUser():\n\nError: {e}",
            # "post_msg"      : f"OrgChartPortal: AddUser():\n\nError: {e}. The exception type is: {e.__class__.__name__}",
        })


def UpdateUser(request):

    if request.method != "POST":
        return JsonResponse({
            "post_success": False,
            "post_msg": "{} HTTP request not supported".format(request.method),
        })


    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: UpdateUser(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "UpdateUser():\n\nUNAUTHENTICATE USER!",
            "post_data": None,
        })


    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "UpdateUser():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    try:
        to_windows_username = json_blob['to_windows_username']
        column_name         = json_blob['column_name']
        new_value           = json_blob['new_value']


        is_admin = user_is_active_admin(remote_user)["isAdmin"]
        if not is_admin:
            raise ValueError("'{}' is not admin and does not have the permission to add a new user".format(remote_user))


        valid_editable_ag_column_names = ['Is Admin', 'Active']
        if column_name not in valid_editable_ag_column_names:
            raise ValueError(f"Not allow to edit the AG Column '{column_name}' in this api")


        if to_windows_username is None:
            raise ValueError(f"windows_username '{to_windows_username}' cannot be null")
        elif to_windows_username == '':
            raise ValueError(f"windows_username '{to_windows_username}' cannot be empty string")
        elif ' ' in to_windows_username:
            raise ValueError(f"windows_username '{to_windows_username}' cannot contain whitespace")


        if column_name == 'Is Admin':
            new_value = new_value.title() ## Convert first char to capital. (Title Case)
            if new_value not in ['True', 'False']:
                raise ValueError(f"Unrecognized is_admin value '{new_value}', must be either 'True' or 'False'")

        if column_name == 'Active':
            new_value = new_value.title() ## Convert first char to capital. (Title Case)
            if new_value not in ['True', 'False']:
                raise ValueError(f"Unrecognized active value '{new_value}', must be either 'True' or 'False'")


        try:
            user = TblUsers.objects.using("OrgChartWrite").get(windows_username=to_windows_username)

            if column_name == 'Is Admin':
                user.is_admin = new_value
            elif column_name == 'Active':
                user.active = new_value
            else:
                raise ValueError(f"column_name '{column_name}' is not a valid editable column in this api")

            user.save(using='OrgChartWrite')
        except ObjectDoesNotExist as e:
            raise ValueError(f"Can't find a user with this windows_username '{to_windows_username}'")

        return JsonResponse({
            "post_success"          : True,
            "post_msg"              : None,
            "to_windows_username"   : to_windows_username,
            "column_name"           : column_name,
            "new_value"             : new_value,
        })

    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"OrgChartPortal: UpdateUser():\n\nError: {e}",
            # "post_msg"      : f"OrgChartPortal: UpdateUser():\n\nError: {e}. The exception type is: {e.__class__.__name__}",
        })


def DeleteUser(request):

    if request.method != "POST":
        return JsonResponse({
            "post_success": False,
            "post_msg": "{} HTTP request not supported".format(request.method),
        })


    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: DeleteUser(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "DeleteUser():\n\nUNAUTHENTICATE USER!",
            "post_data": None,
        })


    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "DeleteUser():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    try:
        windows_username = json_blob['windows_username']

        if windows_username is None:
            raise ValueError("windows_username cannot be null")
        elif windows_username == '':
            raise ValueError("windows_username cannot be empty string")

        is_admin = user_is_active_admin(remote_user)["isAdmin"]
        if not is_admin:
            raise ValueError("'{}' is not admin and does not have the permission to delete a user".format(remote_user))

        try:
            user = TblUsers.objects.using("OrgChartWrite").get(windows_username=windows_username)
            user.delete()
        except ObjectDoesNotExist as e:
            raise ValueError(f"Cannot find user with this username: '{windows_username}'")
        except IntegrityError as e:
            if 'REFERENCE constraint' in str(e):
                raise ValueError(f"Violation of REFERENCE constraint: User still has permissions attached to them, please delete those first. Error happened while trying to delete '{windows_username}' from the user table")
            else:
                raise e
        except Exception as e:
            raise e

        return JsonResponse({
            "post_success"      : True,
            "post_msg"          : None,
            "windows_username"  : windows_username
        })

    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"OrgChartPortal: DeleteUser():\n\nError: {e}",
            # "post_msg"      : f"OrgChartPortal: DeleteUser():\n\nError: {e}. The exception type is: {e.__class__.__name__}",
        })


class ManagePermissionsPageView(generic.ListView):
    template_name       = 'OrgChartPortal.template.managepermissions.html'

    get_success         = False
    get_error           = ""
    client_is_admin     = False

    ag_grid_col_def_json= None
    permissions_json    = []
    user_list           = []
    division_list       = []
    wu_desc_list        = []


    def get_queryset(self):
        # Check for Active Admins
        self.client_is_admin = user_is_active_admin(self.request.user)["isAdmin"]

        ## Get the core data
        try:
            if self.client_is_admin:
                ag_grid_col_def = [ ## Need to format this way for AG Grid
                    {'headerName': 'Windows Username'  , 'field': 'user_id__windows_username'   , 'suppressMovable': True , 'lockPinned': True , 'cellClass': 'notEditableColorCode'}
                    ,{'headerName': 'WU'               , 'field': 'wu__wu'                      , 'suppressMovable': True , 'lockPinned': True , 'cellClass': 'notEditableColorCode'}
                    ,{'headerName': 'Sub Division'     , 'field': 'wu__subdiv'                  , 'suppressMovable': True , 'lockPinned': True , 'cellClass': 'notEditableColorCode'}
                    ,{'headerName': 'Desc'             , 'field': 'wu__wu_desc'                 , 'suppressMovable': True , 'lockPinned': True , 'cellClass': 'notEditableColorCode'}
                    ,{'headerName': 'Delete?'          , 'field': None                          , 'suppressMovable': True , 'lockPinned': True}
                ]
                fields_list = [ each['field'] for each in ag_grid_col_def if each['field'] is not None ]

                self.ag_grid_col_def_json   = json.dumps(list(ag_grid_col_def), cls=DjangoJSONEncoder)
                self.permissions_json       = json.dumps(list(TblPermissionsWorkUnit.objects.using('OrgChartRead').all().order_by('wu').values(*fields_list)), cls=DjangoJSONEncoder)
                self.user_list              = [each['windows_username'] for each in TblUsers.objects.using('OrgChartRead').all().order_by('windows_username').values('windows_username')]
                self.division_list          = [each['subdiv'] for each in TblWorkUnits.objects.using('OrgChartRead').filter(subdiv__isnull=False).values('subdiv').distinct()] ## subidv not null filters out the WU 9999 On-Loan
                self.wu_desc_list           = list(TblWorkUnits.objects.using('OrgChartRead').filter(subdiv__isnull=False).values('wu', 'wu_desc')) ## subidv not null filters out the WU 9999 On-Loan
            else:
                raise ValueError("'{}' is not an Admin, and is not authorized to see this page.".format(self.request.user))

        except Exception as e:
            self.get_success    = False
            self.get_error        = "Exception: ManagePermissionsPageView(): get_queryset(): {}".format(e)
            return None

        self.get_success = True
        return None

    def get_context_data(self, **kwargs):
        try:
            context                         = super().get_context_data(**kwargs)
            context["get_success"]          = self.get_success
            context["get_error"]            = self.get_error
            context["client_is_admin"]      = self.client_is_admin
            context["ag_grid_col_def_json"] = self.ag_grid_col_def_json
            context["permissions_json"]     = self.permissions_json
            context["user_list"]            = self.user_list
            context["division_list"]        = self.division_list
            context["wu_desc_list"]         = self.wu_desc_list
            return context
        except Exception as e:
            self.get_success                = False
            self.get_error                  = "Exception: ManagePermissionsPageView(): get_context_data(): {}".format(e)

            context                         = super().get_context_data(**kwargs)
            context["get_success"]          = self.get_success
            context["get_error"]            = self.get_error
            context["client_is_admin"]      = False
            context["ag_grid_col_def_json"] = self.ag_grid_col_def_json
            context["permissions_json"]     = self.permissions_json
            context["user_list"]            = self.user_list
            context["division_list"]        = self.division_list
            context["wu_desc_list"]         = self.wu_desc_list
            return context


def AddUserPermission(request):

    if request.method != "POST":
        return JsonResponse({
            "post_success": False,
            "post_msg": "{} HTTP request not supported".format(request.method),
        })


    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: AddUserPermission(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "AddUserPermission():\n\nUNAUTHENTICATE USER!",
            "post_data": None,
        })


    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "AddUserPermission():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    try:
        windows_username    = json_blob['windows_username']
        perm_add_by         = json_blob['perm_add_by']
        perm_identifier     = json_blob['perm_identifier']


        is_admin = user_is_active_admin(remote_user)["isAdmin"]
        if not is_admin:
            raise ValueError("'{}' is not admin and does not have the permission to add a new user permission".format(remote_user))


        if windows_username is None:
            raise ValueError(f"windows_username '{windows_username}' cannot be null")
        elif windows_username == '':
            raise ValueError(f"windows_username '{windows_username}' cannot be empty string")

        if perm_identifier is None:
            raise ValueError(f"perm_identifier '{perm_identifier}' cannot be null")
        elif perm_identifier == '':
            raise ValueError(f"perm_identifier '{perm_identifier}' cannot be empty string")

        valid_action_by = ['division', 'wu']
        if perm_add_by not in valid_action_by:
            raise ValueError(f"perm_add_by '{perm_add_by}' must be one of these options {valid_action_by}")


        try:
            user = TblUsers.objects.using("OrgChartWrite").get(windows_username=windows_username)
        except ObjectDoesNotExist as e:
            raise ValueError(f"Could not find a valid user with this windows_username: '{windows_username}'")


        if perm_add_by == 'division':
            workunits = TblWorkUnits.objects.using("OrgChartWrite").filter(subdiv__isnull=False, subdiv=perm_identifier)
            if workunits.count() == 0:
                raise ValueError(f"Could not find any work units related to subdiv: '{perm_identifier}'")

        elif perm_add_by == 'wu':
            workunits = TblWorkUnits.objects.using("OrgChartWrite").filter(wu__isnull=False, wu=perm_identifier)
            if workunits.count() == 0:
                raise ValueError(f"Could not find the work unit related to wu: '{perm_identifier}'")
            elif workunits.count() != 1:
                raise ValueError(f"Found multiple work units related to wu: '{perm_identifier}' (Should only find one)")

        else:
            raise ValueError(f"Unrecognized perm_add_by '{perm_add_by}'. Must be one of these options {valid_action_by}")


        existing_perms = TblPermissionsWorkUnit.objects.using("OrgChartWrite").filter(user_id__windows_username=windows_username)
        if existing_perms.count() > 0:
            ## Filter out any overlaping existing WU permissions
            workunits = workunits.exclude(wu__in=[each.wu.wu for each in existing_perms])

            if workunits.count() == 0:
                raise ValueError(f"'{windows_username}' already has permissions to all the WUs related to '{perm_identifier}'")

        # Save the data in a single atomic transaction
        try:
            with transaction.atomic(using='OrgChartWrite'):
                for each in workunits:
                    new_permission = TblPermissionsWorkUnit(
                        user_id=user
                        ,wu=each
                    )
                    new_permission.save(using='OrgChartWrite')

        except IntegrityError as e:
            if 'UNIQUE KEY constraint' in str(e):
                raise ValueError(f"Violation of UNIQUE KEY constraint: Happened while trying to insert ('{user.windows_username}', '{each.wu}') into work unit permissions table")
            else:
                raise e
        except Exception as e:
            raise


        return JsonResponse({
            "post_success"      : True,
            "post_msg"          : None,
            "windows_username"  : user.windows_username,
            "perm_identifier"   : perm_identifier,
            "wu_added_list"     : list(workunits.values('wu', 'subdiv', 'wu_desc')),
        })
    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"OrgChartPortal: AddUserPermission():\n\nError: {e}",
            # "post_msg"      : f"OrgChartPortal: AddUserPermission():\n\nError: {e}. The exception type is: {e.__class__.__name__}",
        })


def DeleteUserPermission(request):

    if request.method != "POST":
        return JsonResponse({
            "post_success": False,
            "post_msg": "{} HTTP request not supported".format(request.method),
        })


    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: DeleteUserPermission(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "DeleteUserPermission():\n\nUNAUTHENTICATE USER!",
            "post_data": None,
        })


    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: DeleteUserPermission():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    try:
        windows_username    = json_blob['windows_username']
        perm_delete_by      = json_blob['perm_delete_by']
        perm_identifier     = json_blob['perm_identifier']

        is_admin = user_is_active_admin(remote_user)["isAdmin"]
        if not is_admin:
            raise ValueError("'{}' is not admin and does not have the permission to remove user permission".format(remote_user))

        if windows_username is None:
            raise ValueError(f"windows_username '{windows_username}' cannot be null")
        elif windows_username == '':
            raise ValueError(f"windows_username '{windows_username}' cannot be empty string")

        valid_action_by = ['division', 'wu']
        if perm_delete_by not in valid_action_by:
            raise ValueError(f"perm_delete_by '{perm_delete_by}' must be one of these options {valid_action_by}")

        if perm_delete_by == 'division':
            ...
            #@TODO implement this

        elif perm_delete_by == 'wu':
            if perm_identifier is None:
                raise ValueError(f"wu '{perm_identifier}' cannot be null")
            elif perm_identifier == '':
                raise ValueError(f"wu '{perm_identifier}' cannot be empty string")

            try:
                wu_permission = TblPermissionsWorkUnit.objects.using("OrgChartWrite").get(
                    user_id__windows_username=windows_username
                    ,wu__wu=perm_identifier
                )
                wu_permission.delete()
            except ObjectDoesNotExist as e:
                raise ValueError(f"Could not find a valid user permission with this windows_username and wu: '{windows_username}' - '{perm_identifier}'")
            except Exception as e:
                raise e

        else:
            raise ValueError(f"Unrecognized perm_delete_by '{perm_delete_by}'. Must be one of these options {valid_action_by}")

        return JsonResponse({
            "post_success"      : True,
            "post_msg"          : None,
            "windows_username"  : windows_username,
            "perm_identifier"   : perm_identifier,
        })
    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"OrgChartPortal: DeleteUserPermission():\n\nError: {e}",
            # "post_msg"      : f"OrgChartPortal: DeleteUserPermission():\n\nError: {e}. The exception type is: {e.__class__.__name__}",
        })


class HowToUsePageView(TemplateView):
    """Display a PDF with instructions on how to use EmpGridPageView()"""
    template_name = 'OrgChartPortal.template.howtouse.html'

    get_success                     = True
    get_error                       = ""
    client_is_admin                 = False

    def get_context_data(self, **kwargs):
        try:
            context                         = super().get_context_data(**kwargs)
            context["get_success"]          = self.get_success
            context["get_error"]            = self.get_error
            context["client_is_admin"]      = self.client_is_admin
            return context
        except Exception as e:
            self.get_success                = False
            self.get_error                  = "Exception: ManagePermissionsPageView(): get_context_data(): {}".format(e)

            context                         = super().get_context_data(**kwargs)
            context["get_success"]          = self.get_success
            context["get_error"]            = self.get_error
            context["client_is_admin"]      = False
            return context