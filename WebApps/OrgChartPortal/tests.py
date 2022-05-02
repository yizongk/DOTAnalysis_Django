from django.test import Client
import unittest
from .models import *
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.contrib import auth
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import json
from WebAppsMain.settings import TEST_WINDOWS_USERNAME, TEST_PMS, TEST_SUPERVISOR_PMS, TEST_COMMISSIONER_PMS
from WebAppsMain.testing_utils import get_to_api, HttpPostTestCase, HttpGetTestCase
from django.db.models import Max, Q
### DO NOT RUN THIS IN PROD ENVIRONMENT


DEFAULT_WORK_UNIT = '1600'


def get_or_create_user(windows_username=TEST_WINDOWS_USERNAME):
    """create or get an user and return the user object. Defaults to TEST_WINDOWS_USERNAME as the user"""
    try:
        wu = TblWorkUnits.objects.using('OrgChartWrite').get(
            wu__exact=DEFAULT_WORK_UNIT
        )

        pms = TblEmployees.objects.using('OrgChartWrite').get_or_create(
            pms=TEST_PMS
        )[0]
        pms.lv='B'
        pms.wu=wu
        pms.save(using='OrgChartWrite')

        return TblUsers.objects.using('OrgChartWrite').get_or_create(
            windows_username=windows_username
            ,pms=pms
        )[0]
    except Exception as e:
        raise ValueError(f"get_or_create_user(): {e}")


def grant_admin_status(windows_username=TEST_WINDOWS_USERNAME):
    """create or get an user and set it up with admin status and return the user object. Defaults to TEST_WINDOWS_USERNAME as the user"""
    try:
        user = get_or_create_user(windows_username=windows_username)
        user.is_admin=True
        user.active=True
        user.save(using='OrgChartWrite')
        return user
    except Exception as e:
            raise ValueError(f"grant_admin_status(): {e}")


def remove_admin_status(windows_username=TEST_WINDOWS_USERNAME):
    """removes the admin status of an user"""
    try:
        user = get_or_create_user(windows_username=windows_username)
        user.is_admin=False
        user.save(using='OrgChartWrite')
        return user
    except Exception as e:
            raise ValueError(f"remove_admin_status(): {e}")


def set_up_permissions(windows_username=TEST_WINDOWS_USERNAME, work_units=[DEFAULT_WORK_UNIT]):
    """
        set up permissions for a user. If user is admin, the permissions added will probably mean nothing.

        @windows_username is self explanatory, just one name
        @work_units should be a list of work units
    """
    try:
        for work_unit in work_units:

            work_unit_obj = TblWorkUnits.objects.using('OrgChartWrite').get(
                wu__exact=work_unit
                ,active=True
            )

            user_obj = get_or_create_user(windows_username=windows_username)
            permission = TblPermissionsWorkUnit.objects.using('OrgChartWrite').get_or_create(
                user_id=user_obj
                ,wu=work_unit_obj
            )[0]
            permission.save(using="OrgChartWrite")

    except Exception as e:
        raise ValueError(f"set_up_permissions(): {e}")


def tear_down_permissions(windows_username=TEST_WINDOWS_USERNAME):
    """remove all permissions for an user. If user is admin, the permissions removed will probably mean nothing."""
    try:
        permissions = TblPermissionsWorkUnit.objects.using('OrgChartWrite').filter(
            user_id__windows_username__exact=windows_username
        )

        for each in permissions:
            each.delete(using='OrgChartWrite')
    except Exception as e:
            raise ValueError(f"tear_down_permissions_for_user(): {e}")


def tear_down(windows_username=TEST_WINDOWS_USERNAME):
    """Removes admin status of @windows_username, and set all its permissions to inactive. Defaults to TEST_WINDOWS_USERNAME"""
    try:
        remove_admin_status(windows_username=windows_username)
        tear_down_permissions(windows_username=windows_username)
    except Exception as e:
        raise ValueError(f"tear_down(): {e}")


def get_active_lv_list():
    return ['B', 'C', 'K', 'M', 'N', 'Q', 'R', 'S']


def get_active_tblemployee_qryset():
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

        return TblEmployees.objects.using('OrgChartRead').filter(
            Q( lv__in=get_active_lv_list() )
            | Q( pms__in=active_L_pms_list )
        )
    except Exception as e:
        raise ValueError(f"get_active_tblemployee_qryset(): {e}")


class TestViewPagesResponse(HttpGetTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        set_up_permissions()

        self.regular_views = [
            'orgchartportal_home_view',
            'orgchartportal_about_view',
            'orgchartportal_contact_view',
            'orgchartportal_empgrid_view',
            'orgchartportal_orgchart_view',
            'orgchartportal_how_to_use_view',
        ]

        self.admin_views = [
            'orgchartportal_admin_panel_view',
            'orgchartportal_manage_users_view',
            'orgchartportal_manage_permissions_view',
        ]

        self.additional_context_requirements_normal = [
            {
                'view'                      : 'orgchartportal_empgrid_view'
                ,'additional_context_keys'  : [
                                                'emp_entry_columns_json'
                                                ,'emp_entries_json'
                                                ,'supervisor_dropdown_list_json'
                                                ,'site_dropdown_list_json'
                                                ,'site_floor_dropdown_list_json'
                                                ,'site_type_dropdown_list_json'
                                            ]
                ,'qa_fct'                   : self.__assert_additional_context_qa_empgrid
            }
            ## Rest qa_fct are left None because those are admin views and aren't meant to return data
            ,{
                'view'                      : 'orgchartportal_manage_users_view'
                ,'additional_context_keys'  : [
                                                'ag_grid_col_def_json'
                                                ,'users_data_json'
                                            ]
                ,'qa_fct'                   : None
            }
            ,{
                'view'                      : 'orgchartportal_manage_permissions_view'
                ,'additional_context_keys'  : [
                                                'ag_grid_col_def_json'
                                                ,'permissions_json'
                                                ,'user_list'
                                                ,'division_list'
                                                ,'wu_desc_list'
                                            ]
                ,'qa_fct'                   : None
            }
        ]

        self.additional_context_requirements_admin = [
            {
                'view'                      : 'orgchartportal_empgrid_view'
                ,'additional_context_keys'  : [
                                                'emp_entry_columns_json'
                                                ,'emp_entries_json'
                                                ,'supervisor_dropdown_list_json'
                                                ,'site_dropdown_list_json'
                                                ,'site_floor_dropdown_list_json'
                                                ,'site_type_dropdown_list_json'
                                            ]
                ,'qa_fct'                   : self.__assert_additional_context_qa_empgrid
            }
            ,{
                'view'                      : 'orgchartportal_manage_users_view'
                ,'additional_context_keys'  : [
                                                'ag_grid_col_def_json'
                                                ,'users_data_json'
                                            ]
                ,'qa_fct'                   : self.__assert_additional_context_qa_manage_users
            }
            ,{
                'view'                      : 'orgchartportal_manage_permissions_view'
                ,'additional_context_keys'  : [
                                                'ag_grid_col_def_json'
                                                ,'permissions_json'
                                                ,'user_list'
                                                ,'division_list'
                                                ,'wu_desc_list'
                                            ]
                ,'qa_fct'                   : self.__assert_additional_context_qa_manage_permissions
            }
        ]

    @classmethod
    def tearDownClass(self):
        tear_down()

    def __assert_additional_context_qa_empgrid(self, response):
        ## Make sure the emp_entry_columns_json got all the required fields
        emp_entry_columns_dict  = json.loads(response.context_data['emp_entry_columns_json'])
        from_api_fields         = set(each['field'] for each in emp_entry_columns_dict)
        required_fields             = set([
            'pms'
            ,'last_name'
            ,'first_name'
            ,'lv'
            ,'wu__wu'
            ,'civil_title'
            ,'office_title'
            ,'supervisor_pms__pms'
            ,'actual_site_id__site_id'
            ,'actual_floor_id__floor_id'
            ,'actual_site_type_id__site_type_id'])
        if len(from_api_fields) > len(required_fields):
            raise ValueError(f"orgchartportal_empgrid_view: context variable emp_entry_columns_json got back more fields than expected. These are the unexpected fields: {from_api_fields - required_fields}")
        self.assertTrue(from_api_fields == required_fields
            ,f'orgchartportal_empgrid_view: context variable emp_entry_columns_json is missing some fields: {required_fields -  from_api_fields}')

        ## Make sure emp_entries_json has only WUs that client has permission to
        emp_entries_dict    = json.loads(response.context_data['emp_entries_json'])
        distinct_wu         = set(each['wu__wu'] for each in emp_entries_dict)
        user = get_or_create_user(windows_username=TEST_WINDOWS_USERNAME)
        if user.is_admin:
            permissions_wu  = set(each.wu for each in TblWorkUnits.objects.using('OrgChartRead').all())
        else:
            permissions_wu  = set(each.wu.wu for each in TblPermissionsWorkUnit.objects.using('OrgChartRead').filter(user_id__windows_username__exact=TEST_WINDOWS_USERNAME, is_active=True))
        if len(permissions_wu) > len(distinct_wu):
            missing_wus = permissions_wu - distinct_wu
            if get_active_tblemployee_qryset().filter(wu__wu__in=missing_wus).count() == 0:
                ## the missing_wus actually doesn't exists in the active list of employees, no error here, remove it from list and moving on.
                permissions_wu = permissions_wu - missing_wus
            else:
                raise ValueError(f"orgchartportal_empgrid_view: Did not get back any emp with these Work Units even though permission allows it: {missing_wus}")
        self.assertTrue(distinct_wu == permissions_wu
            ,f'orgchartportal_empgrid_view: Got back an entry with work unit that "{TEST_WINDOWS_USERNAME}" does not have permission to. Here are the Work Units that it got, but should not have {distinct_wu - permissions_wu}"')

        ## Make sure a list of all active employees is returned in supervisor dropdown
        supervisor_dropdown_dict    = json.loads(response.context_data['supervisor_dropdown_list_json'])
        count_of_all_api            = len([each for each in supervisor_dropdown_dict])
        count_of_all_base           = len([each for each in get_active_tblemployee_qryset()])
        self.assertTrue(count_of_all_base == count_of_all_api
            ,f'orgchartportal_empgrid_view: Did not get back a list of ALL active employees in the supervisor_dropdown_list_json context variable. base {count_of_all_base} vs api {count_of_all_api}')

        ## Make sure a list of all sites is returned in site dropdown
        site_dropdown_dict  = json.loads(response.context_data['site_dropdown_list_json'])
        count_of_all_api    = len([each for each in site_dropdown_dict])
        count_of_all_base   = len([each for each in TblDOTSites.objects.using('OrgChartRead').all()])
        self.assertTrue(count_of_all_base == count_of_all_api
            ,f'orgchartportal_empgrid_view: Did not get back a list of ALL sites in the site_dropdown_list_json context variable. base {count_of_all_base} vs api {count_of_all_api}')

        ## Make sure a list of all site floors is returned in site floor dropdown
        site_floor_dropdown_dict    = json.loads(response.context_data['site_floor_dropdown_list_json'])
        count_of_all_api            = len([each for each in site_floor_dropdown_dict])
        count_of_all_base           = len([each for each in TblDOTSiteFloors.objects.using('OrgChartRead').all()])
        self.assertTrue(count_of_all_base == count_of_all_api
            ,f'orgchartportal_empgrid_view: Did not get back a list of ALL site floors in the site_floor_dropdown_list_json context variable. base {count_of_all_base} vs api {count_of_all_api}')

        ## Make sure a list of all site type site floors is returned in site type dropdown
        site_type_dropdown_dict     = json.loads(response.context_data['site_type_dropdown_list_json'])
        count_of_all_api            = len([each for each in site_type_dropdown_dict])
        count_of_all_base           = len([each for each in TblDOTSiteFloorSiteTypes.objects.using('OrgChartRead').values(
                                        'site_type_id__site_type_id'
                                        ,'site_type_id__site_type'
                                        ,'floor_id__floor_id'
                                        ,'floor_id__site_id'
                                    ).all()])
        self.assertTrue(count_of_all_base == count_of_all_api
            ,f'orgchartportal_empgrid_view: Did not get back a list of ALL site floor + site types in the site_type_dropdown_list_json context variable. base {count_of_all_base} vs api {count_of_all_api}')

    def __assert_additional_context_qa_manage_users(self, response):
        ## Make sure the ag_grid_col_def_json got all the required fields
        ag_grid_col_def_dict    = json.loads(response.context_data['ag_grid_col_def_json'])
        from_api_fields         = set(each['field'] for each in ag_grid_col_def_dict)
        required_fields         = set([
                                    'pms'
                                    ,'windows_username'
                                    ,'is_admin'
                                    ,'active'
                                    ,None
                                ])
        if len(from_api_fields) > len(required_fields):
            raise ValueError(f"orgchartportal_manage_users_view: context variable ag_grid_col_def_json got back more fields than expected. These are the unexpected fields: {from_api_fields - required_fields}")
        self.assertTrue(from_api_fields == required_fields
            ,f'orgchartportal_manage_users_view: context variable ag_grid_col_def_json is missing some fields: {required_fields -  from_api_fields}')

        ## Make sure users_data_json has ALL the user records, since this api is an admin api
        users_data_json         = json.loads(response.context_data['users_data_json'])
        from_api_users_data     = set(each['windows_username'] for each in users_data_json)
        required_users_data     = set(each.windows_username for each in TblUsers.objects.using('OrgChartRead').all())
        self.assertEqual(from_api_users_data, required_users_data
            ,f"orgchartportal_manage_users_view: context variable users_data_json either has more data than allowed ({from_api_users_data - required_users_data}) or has less data than allowed ({required_users_data - from_api_users_data})")

    def __assert_additional_context_qa_manage_permissions(self, response):
        ## Make sure the ag_grid_col_def_json got all the required fields
        ag_grid_col_def_dict    = json.loads(response.context_data['ag_grid_col_def_json'])
        from_api_fields         = set(each['field'] for each in ag_grid_col_def_dict)
        required_fields         = set([
                                    'user_id__windows_username'
                                    ,'wu__wu'
                                    ,'wu__subdiv'
                                    ,'wu__wu_desc'
                                    ,None
                                ])
        if len(from_api_fields) > len(required_fields):
            raise ValueError(f"orgchartportal_manage_permissions_view: context variable ag_grid_col_def_json got back more fields than expected. These are the unexpected fields: {from_api_fields - required_fields}")
        self.assertTrue(from_api_fields == required_fields
            ,f'orgchartportal_manage_permissions_view: context variable ag_grid_col_def_json is missing some fields: {required_fields -  from_api_fields}')

        ## Make sure permissions_json has ALL the permission records, since this api is an admin api
        permissions_json        = json.loads(response.context_data['permissions_json'])
        from_api_permissions    = set(f"{each['user_id__windows_username']}-{each['wu__wu']}" for each in permissions_json)
        required_permissions    = set(f"{each.user_id.windows_username}-{each.wu.wu}" for each in TblPermissionsWorkUnit.objects.using('OrgChartRead').all())
        self.assertEqual(from_api_permissions, required_permissions
            ,f"orgchartportal_manage_permissions_view: context variable permissions_json either has more data than allowed ({from_api_permissions - required_permissions}) or has less data than allowed ({required_permissions - from_api_permissions})")

        from_api_user_list      = set(response.context_data['user_list'])
        from_api_division_list  = set(response.context_data['division_list'])
        from_api_wu_desc_list   = set(each['wu'] for each in response.context_data['wu_desc_list'])

        required_user_list      = set(each.windows_username  for each in TblUsers.objects.using('OrgChartRead').all())
        required_division_list  = set(each.subdiv            for each in TblWorkUnits.objects.using('OrgChartRead').filter(subdiv__isnull=False).distinct()) ## subidv not null filters out the WU 9999 On-Loan
        required_wu_desc_list   = set(each.wu                for each in TblWorkUnits.objects.using('OrgChartRead').filter(subdiv__isnull=False)) ## subidv not null filters out the WU 9999 On-Loan

        self.assertEqual(from_api_user_list, required_user_list
            ,f"orgchartportal_manage_permissions_view: context variable user_list either has more data than allowed ({from_api_user_list - required_user_list}) or has less data than allowed ({required_user_list - from_api_user_list})")
        self.assertEqual(from_api_division_list, required_division_list
            ,f"orgchartportal_manage_permissions_view: context variable division_list either has more data than allowed ({from_api_division_list - required_division_list}) or has less data than allowed ({required_division_list - from_api_division_list})")
        self.assertEqual(from_api_wu_desc_list, required_wu_desc_list
            ,f"orgchartportal_manage_permissions_view: context variable wu_desc_list either has more data than allowed ({from_api_wu_desc_list - required_wu_desc_list}) or has less data than allowed ({required_wu_desc_list - from_api_wu_desc_list})")

    def test_views_response_status_200(self):
        """Test normal user"""
        remove_admin_status()
        self.assert_response_status_200()

        """Test admin user"""
        grant_admin_status()
        self.assert_response_status_200()

    def test_views_response_user_admin_restriction(self):
        """Test normal user, should only have acess to regular views"""
        remove_admin_status()
        self.assert_user_access_on_normal_and_admin_view()

        """Test admin user, should have access to all views"""
        grant_admin_status()
        self.assert_admin_access_on_normal_and_admin_view()

    def test_views_response_data(self):
        """
            Test views to have the required GET request context data
            Some views have additional context data, need to test for those here
        """
        # Test normal user
        remove_admin_status()
        self.assert_additional_context_data(additional_requirements=self.additional_context_requirements_normal)

        # Test admin user
        grant_admin_status()
        self.assert_additional_context_data(additional_requirements=self.additional_context_requirements_admin)


class TestAPIUpdateEmployeeData(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        self.api_name   = 'orgchartportal_update_employee_data'
        self.post_response_json_key_specifications = []


        tear_down()
        set_up_permissions()
        self.test_pms   = TEST_PMS

        self.__null_out_test_pms_obj(self)

        ## Sequence 0, should work anytime
        self.valid_payload0 = [
            {
                'to_pms'        : self.test_pms
                ,'column_name'  : 'Supervisor'
                ,'new_value'    : TEST_SUPERVISOR_PMS
            }
            ,{
                'to_pms'        : self.test_pms
                ,'column_name'  : 'Office Title'
                ,'new_value'    : 'Hello World!'
            }
            ,{
                'to_pms'        : self.test_pms
                ,'column_name'  : 'Site'
                ,'new_value'    : 'BK.H'
            }
            ,{
                'to_pms'        : self.test_pms
                ,'column_name'  : 'Floor'
                ,'new_value'    : 'BK.H.1'
            }
            ,{
                'to_pms'        : self.test_pms
                ,'column_name'  : 'Site Type'
                ,'new_value'    : '13'
            }
        ]
        ## Sequence 1: Test auto null out of site floor and site type when site is changed
        self.valid_payload1 = [
            {
                'to_pms'        : self.test_pms
                ,'column_name'  : 'Site'
                ,'new_value'    : 'MN.H'
            }
        ]
        ## Sequence 2: Test null out of site type when site floor is changed, must use a floor id that has multiple possible site type to it, so it doesn't trigger the API's auto populate of site type id if there's only one possible site type id
        self.valid_payload2 = [
            {
                'to_pms'        : self.test_pms
                ,'column_name'  : 'Site'
                ,'new_value'    : 'BK.D'
            },{
                'to_pms'        : self.test_pms
                ,'column_name'  : 'Floor'
                ,'new_value'    : 'BK.D.2'
            }
        ]
        ## Sequence 3: Test auto set site type when site floor has only one site type, like 'MN.H.9'
        self.valid_payload3 = [
            {
                'to_pms'        : self.test_pms
                ,'column_name'  : 'Site'
                ,'new_value'    : 'MN.H'
            },{ ## Floor change to MN.H.9 should also set the actual stie type since there's only one valid floor site for that site floor. Make sure to check it in the '## Check if data was saved correctly and if tblChanges was updated correctly' section
                'to_pms'        : self.test_pms
                ,'column_name'  : 'Floor'
                ,'new_value'    : 'MN.H.9'
            }
        ]
        ## Sequence 4: Test site type direct update, but first will need to reset site floor to another site floor with multiple site types
        self.valid_payload4 = [
            {
                'to_pms'        : self.test_pms
                ,'column_name'  : 'Site'
                ,'new_value'    : 'BK.B'
            },{
                'to_pms'        : self.test_pms
                ,'column_name'  : 'Floor'
                ,'new_value'    : 'BK.B.1'  ## Should accept 7 or 3 for site type
            },{
                'to_pms'        : self.test_pms
                ,'column_name'  : 'Site Type'
                ,'new_value'    : '3'
            }
            ,{
                'to_pms'        : self.test_pms
                ,'column_name'  : 'Site Type'
                ,'new_value'    : '7'
            }
        ]

    @classmethod
    def tearDownClass(self):
        self.__null_out_test_pms_obj(self)
        tear_down()

    def test_with_valid_data(self):
        ## Sequence 0
        self.__null_out_test_pms_obj()
        for payload in self.valid_payload0:
            self.assert_post_with_valid_payload_is_success(payload=payload)

            ## Check if data was saved correctly and if tblChanges was updated correctly
            saved_object = TblEmployees.objects.using('OrgChartRead').get(
                pms=self.test_pms
            )

            if payload['column_name'] == 'Supervisor':
                self.assert_post_key_update_equivalence(key_name=payload['column_name'], key_value=payload['new_value'], db_value=saved_object.supervisor_pms.pms)
                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='SupervisorPMS', proposed_new_value=payload['new_value'])
            elif payload['column_name'] == 'Office Title':
                self.assert_post_key_update_equivalence(key_name=payload['column_name'], key_value=payload['new_value'], db_value=saved_object.office_title)
                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='OfficeTitle', proposed_new_value=payload['new_value'])
            elif payload['column_name'] == 'Site':
                self.assert_post_key_update_equivalence(key_name=payload['column_name'], key_value=payload['new_value'], db_value=saved_object.actual_site_id.site_id)
                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='ActualSiteId', proposed_new_value=payload['new_value'])
            elif payload['column_name'] == 'Floor':
                self.assert_post_key_update_equivalence(key_name=payload['column_name'], key_value=payload['new_value'], db_value=saved_object.actual_floor_id.floor_id)
                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='ActualFloorId', proposed_new_value=payload['new_value'])
            elif payload['column_name'] == 'Site Type':
                self.assert_post_key_update_equivalence(key_name=payload['column_name'], key_value=payload['new_value'], db_value=saved_object.actual_site_type_id.site_type_id)
                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='ActualSiteTypeId', proposed_new_value=payload['new_value'])
            else:
                raise ValueError(f"uncaught payload param value in test case (Remove it, or add a test case for it): '{payload['column_name']}'")

        ## Sequence 1 - Test auto null out of site floor and site type when site is changed
        self.__null_out_test_pms_obj()
        ### Random value set to floor and site type to test the null out
        test_emp = TblEmployees.objects.using('OrgChartWrite').get(
            pms=self.test_pms
        )
        test_emp.actual_floor_id        = TblDOTSiteFloors.objects.using('OrgChartWrite').get(floor_id__exact='BK.E.16')
        test_emp.actual_site_type_id    = TblDOTSiteTypes.objects.using('OrgChartWrite').get(site_type_id__exact='3')
        test_emp.save(using='OrgChartWrite')
        for payload in self.valid_payload1:
            self.assert_post_with_valid_payload_is_success(payload=payload)

            ## Check if data was saved correctly and if tblChanges was updated correctly
            saved_object = TblEmployees.objects.using('OrgChartRead').get(
                pms=self.test_pms
            )

            if payload['column_name'] == 'Site':
                self.assert_post_key_update_equivalence(key_name=payload['column_name'], key_value=payload['new_value'], db_value=saved_object.actual_site_id.site_id)
                self.assert_post_key_update_equivalence(key_name='Change Site -> Auto Null out of Site Floor', key_value=None, db_value=saved_object.actual_floor_id)
                self.assert_post_key_update_equivalence(key_name='Change Site -> Auto Null out of Site Type', key_value=None, db_value=saved_object.actual_site_type_id)

                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='ActualSiteId', proposed_new_value=payload['new_value'])
                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='ActualFloorId', proposed_new_value=None)
                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='ActualSiteTypeId', proposed_new_value=None)
            else:
                raise ValueError(f"uncaught payload param value in test case (Remove it, or add a test case for it): '{payload['column_name']}'")

        ## Sequence 2 - Test null out of site type when site floor is changed
        self.__null_out_test_pms_obj()
        ### Random value set to site type to test the null out
        test_emp = TblEmployees.objects.using('OrgChartWrite').get(
            pms=self.test_pms
        )
        test_emp.actual_site_type_id    = TblDOTSiteTypes.objects.using('OrgChartWrite').get(site_type_id__exact='3')
        test_emp.save(using='OrgChartWrite')
        for payload in self.valid_payload2:
            self.assert_post_with_valid_payload_is_success(payload=payload)

            ## Check if data was saved correctly and if tblChanges was updated correctly
            saved_object = TblEmployees.objects.using('OrgChartRead').get(
                pms=self.test_pms
            )

            if payload['column_name'] == 'Site':
                self.assert_post_key_update_equivalence(key_name=payload['column_name'], key_value=payload['new_value'], db_value=saved_object.actual_site_id.site_id)

                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='ActualSiteId', proposed_new_value=payload['new_value'])
            elif payload['column_name'] == 'Floor':
                self.assert_post_key_update_equivalence(key_name=payload['column_name'], key_value=payload['new_value'], db_value=saved_object.actual_floor_id.floor_id)
                self.assert_post_key_update_equivalence(key_name='Change Floor -> Auto Null out of Site Type', key_value=None, db_value=saved_object.actual_site_type_id)

                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='ActualFloorId', proposed_new_value=payload['new_value'])
                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='ActualSiteTypeId', proposed_new_value=None)
            else:
                raise ValueError(f"uncaught payload param value in test case (Remove it, or add a test case for it): '{payload['column_name']}'")

        ## Sequence 3 - Test auto set site type when site floor has only one site type, like 'MN.H.9'
        self.__null_out_test_pms_obj()
        for payload in self.valid_payload3:
            self.assert_post_with_valid_payload_is_success(payload=payload)

            ## Check if data was saved correctly and if tblChanges was updated correctly
            saved_object = TblEmployees.objects.using('OrgChartRead').get(
                pms=self.test_pms
            )

            if payload['column_name'] == 'Site':
                ## A change of Site should also null out site floor and site type. Check if data saved, and tracked in tblChanges
                self.assert_post_key_update_equivalence(key_name=payload['column_name']                     , key_value=payload['new_value'], db_value=saved_object.actual_site_id.site_id)
                self.assert_post_key_update_equivalence(key_name='Change Site -> Auto Null out of Floor'    , key_value=None                , db_value=saved_object.actual_floor_id)
                self.assert_post_key_update_equivalence(key_name='Change Site -> Auto Null out of Site Type', key_value=None                , db_value=saved_object.actual_site_type_id)

                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='ActualSiteId'     , proposed_new_value=payload['new_value'])
                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='ActualFloorId'    , proposed_new_value=None)
                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='ActualSiteTypeId' , proposed_new_value=None)
            elif payload['column_name'] == 'Floor':
                ## 'MN.H.9' should also have set site type id to 7
                self.assert_post_key_update_equivalence(key_name=payload['column_name'], key_value=payload['new_value'] , db_value=saved_object.actual_floor_id.floor_id)
                self.assert_post_key_update_equivalence(key_name=payload['column_name'], key_value='7'                  , db_value=saved_object.actual_site_type_id.site_type_id)

                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='ActualFloorId'    , proposed_new_value=payload['new_value'])
                self.__assert_delta_tracked_in_tblChanges(proposed_by_pms=self.test_pms, proposed_to_pms=payload['to_pms'], proposed_column_name='ActualSiteTypeId' , proposed_new_value='7')
            else:
                raise ValueError(f"uncaught payload param value in test case (Remove it, or add a test case for it): '{payload['column_name']}'")

    def test_data_validation(self):
        f"""Testing {self.api_name} data validation"""

        payloads = self.valid_payload0
        parameters = [
            # Parameter name    # Accepted type
            "to_pms"            # str   -> int formatted str of len 7
            ,"column_name"      # str   -> must be one of the follow ['Supervisor', 'Office Title', 'Site', 'Floor', 'Site Type']
            ,"new_value"        # str   -> depends on the @column_name that was given
        ]
        for payload in payloads:
            for param_name in parameters:

                if param_name == 'to_pms':
                    valid   = [self.test_pms]
                    invalid = ['a', 1, 2.3, None, True, 'a123456', '12345678']
                elif param_name == 'column_name':
                    valid   = ['Supervisor', 'Office Title', 'Site', 'Floor', 'Site Type']
                    invalid = ['a', 1, 2.3, None, True]
                elif param_name == 'new_value':
                    if payload['column_name'] == 'Supervisor':
                        valid   = [TEST_SUPERVISOR_PMS]
                        invalid = ['a', 1, 2.3, None, True, 'a123456', '12345678']
                    elif payload['column_name'] == 'Office Title':
                        valid   = ['Test Office Title Input']
                        invalid = [1, 2.3, None, True]
                    elif payload['column_name'] == 'Site':
                        valid   = ['BK.H']
                        invalid = ['a', 1, 2.3, None, True]
                    elif payload['column_name'] == 'Floor':
                        valid   = ['BK.H.1']
                        invalid = ['a', 1, 2.3, None, True]
                    elif payload['column_name'] == 'Site Type':
                        valid   = ['13']
                        invalid = ['a', 1, 2.3, None, True]
                else:
                    raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

                def special_param_good_cond(res_content):
                    if (
                        (res_content['post_success'] == True)
                        or (
                            res_content['post_success'] == False
                            and any([
                                'No change in data, no update needed.' in res_content['post_msg']       ## this error message in save() only gets called when it all pass data validation
                                ]))):
                        return True
                    else:
                        return False

                def special_param_good_cond_for_column_name(res_content):
                    if (
                        (res_content['post_success'] == True)
                        or (
                            res_content['post_success'] == False
                            and any([
                                'is not an editable column' not in res_content['post_msg']      ## for column_names, it will only fail data validation if error message is a specific one
                                ]))):
                        return True
                    else:
                        return False

                for data in valid:
                    if param_name == 'column_name':
                        self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data, param_is_good_fct=special_param_good_cond_for_column_name)
                    else:
                        self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data, param_is_good_fct=special_param_good_cond)

                for data in invalid:
                    self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)

    def __null_out_test_pms_obj(self):
        test_pms_obj = TblEmployees.objects.using('OrgChartWrite').get(pms=self.test_pms)
        test_pms_obj.supervisor_pms         = None
        test_pms_obj.office_title           = None
        test_pms_obj.actual_site_id         = None
        test_pms_obj.actual_floor_id        = None
        test_pms_obj.actual_site_type_id    = None
        test_pms_obj.save(using='OrgChartWrite')

    def __get_latest_changes_obj_by(self, by_pms, to_pms, column_name):
        try:
            return TblChanges.objects.using('OrgChartRead').filter(
                updated_by_pms__exact=by_pms
                ,updated_to_pms__exact=to_pms
                ,column_name__exact=column_name
            ).order_by('-updated_on').first()
        except:
            raise

    def __assert_delta_tracked_in_tblChanges(self, proposed_by_pms, proposed_to_pms, proposed_column_name, proposed_new_value):
        saved_change_obj = self.__get_latest_changes_obj_by(by_pms=proposed_by_pms, to_pms=proposed_to_pms, column_name=proposed_column_name)
        self.assert_post_key_update_equivalence(key_name=f"tblChanges: track change of '{proposed_column_name}' failed", key_value=proposed_new_value, db_value=saved_change_obj.new_value)


class TestAPIGetClientWUPermissions(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        self.api_name   = 'orgchartportal_get_client_wu_permissions_list'
        self.post_response_json_key_specifications = [
            {'name': 'wu_permissions', 'null': True}
        ]

        tear_down()
        set_up_permissions()

        self.client_usr_obj = get_or_create_user()
        self.valid_payload = {}

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_with_valid_data(self):
        remove_admin_status()
        payload             = self.valid_payload
        response_content    = self.assert_post_with_valid_payload_is_success(payload=payload)

        ## Check if data was queried correctly
        wu_permissions_query = TblPermissionsWorkUnit.objects.using('OrgChartRead').filter(
                user_id__windows_username=self.client_usr_obj.windows_username
                ,user_id__active=True
                ,is_active=True
            )
        wu_permissions_required = set(each.wu.wu for each in wu_permissions_query)

        self.assert_post_key_lookup_equivalence(key_name='wu_permissions', key_value=set(each['wu__wu'] for each in response_content['post_data']['wu_permissions']), db_value=wu_permissions_required)


        grant_admin_status()
        payload             = self.valid_payload
        response_content    = self.assert_post_with_valid_payload_is_success(payload=payload)

        ## For admins, the post_success must be true, and post_msg should be "User is Admin"
        self.assert_post_key_lookup_equivalence(key_name='post_msg', key_value=response_content['post_msg'], db_value="User is Admin")

    def test_data_validation(self):
        pass ## This api doesn't take in any params


class TestAPIGetClientTeammates(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        self.api_name   = 'orgchartportal_get_client_teammates_list'
        self.post_response_json_key_specifications = [
            {'name': 'teammates', 'null': True}
        ]

        tear_down()
        set_up_permissions()

        self.client_usr_obj = get_or_create_user()
        self.valid_payload = {}

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_with_valid_data(self):
        remove_admin_status()
        payload             = self.valid_payload
        response_content    = self.assert_post_with_valid_payload_is_success(payload=payload)

        ## Check if data was queried correctly
        wu_permissions_query = TblPermissionsWorkUnit.objects.using('OrgChartRead').filter(
                user_id__windows_username=self.client_usr_obj.windows_username
                ,user_id__active=True
            )
        wu_permissions_list = wu_permissions_query.values('wu__wu')
        teammates_query = TblPermissionsWorkUnit.objects.using('OrgChartRead').filter(
            wu__wu__in=wu_permissions_list
            ,user_id__active=True
            ,is_active=True
        )

        teammates_required = set(each.user_id.pms.pms for each in teammates_query)

        self.assert_post_key_lookup_equivalence(key_name='teammates', key_value=sorted(set(each['user_id__pms__pms'] for each in response_content['post_data']['teammates'])), db_value=sorted(teammates_required))


        grant_admin_status()
        payload             = self.valid_payload
        response_content    = self.assert_post_with_valid_payload_is_success(payload=payload)

        ## For admins, the post_success must be true, and post_msg should be "User is Admin"
        self.assert_post_key_lookup_equivalence(key_name='post_msg', key_value=response_content['post_msg'], db_value="User is Admin")

    def test_data_validation(self):
        pass ## This api doesn't take in any params


class TestAPIGetEmpGridStats(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        self.api_name   = 'orgchartportal_get_emp_grid_stats'
        self.post_response_json_key_specifications = [
            {'name': 'supervisor_completed'                     , 'null': True}
            ,{'name': 'office_title_completed'                  , 'null': True}
            ,{'name': 'list_last_updated_on_est'                , 'null': True}
            ,{'name': 'list_last_updated_by'                    , 'null': True}
            ,{'name': 'inactive_supervisor_list'                , 'null': True}
            ,{'name': 'empty_or_invalid_floor_combo_list'       , 'null': True}
            ,{'name': 'empty_or_invalid_site_type_combo_list'   , 'null': True}
        ]

        tear_down()
        set_up_permissions()

        self.valid_payload = {}

    @classmethod
    def tearDownClass(self):
        tear_down()

    def __assert_stats_types(self, response_content):
        self.assert_post_key_lookup_equivalence(key_name='supervisor_completed', key_value=type(response_content['post_data']['supervisor_completed']), db_value=type(99.99))
        self.assert_post_key_lookup_equivalence(key_name='office_title_completed', key_value=type(response_content['post_data']['office_title_completed']), db_value=type(99.99))
        try:
            test = datetime.strptime(response_content['post_data']['list_last_updated_on_est'], "%m/%d/%Y %I:%M:%S %p")
        except Exception as e:
            self.assertTrue(False
                ,f"{response_content['post_data']['list_last_updated_on_est']} is not a valid datetime string in the format of '%m/%d/%Y %I:%M:%S %p': {e}")
        self.assert_post_key_lookup_equivalence(key_name='list_last_updated_by', key_value=type(response_content['post_data']['list_last_updated_by']), db_value=type(''))
        self.assert_post_key_lookup_equivalence(key_name='inactive_supervisor_list', key_value=type(response_content['post_data']['inactive_supervisor_list']), db_value=type([]))
        self.assert_post_key_lookup_equivalence(key_name='empty_or_invalid_floor_combo_list', key_value=type(response_content['post_data']['empty_or_invalid_floor_combo_list']), db_value=type([]))
        self.assert_post_key_lookup_equivalence(key_name='empty_or_invalid_site_type_combo_list', key_value=type(response_content['post_data']['empty_or_invalid_site_type_combo_list']), db_value=type([]))

    def test_with_valid_data(self):
        remove_admin_status()
        payload             = self.valid_payload
        response_content    = self.assert_post_with_valid_payload_is_success(payload=payload)

        ## Check if data type was returned correctly. No data accuracy check here at the moment.
        self.__assert_stats_types(response_content=response_content)


        grant_admin_status()
        payload             = self.valid_payload
        response_content    = self.assert_post_with_valid_payload_is_success(payload=payload)

        ## For admins, the post_success must be true, and post_msg should be "User is Admin"
        self.__assert_stats_types(response_content=response_content)

    def test_data_validation(self):
        pass ## This api doesn't take in any params


class TestAPIEmpGridGetCsvExport(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        self.api_name   = 'orgchartportal_emp_grid_get_csv_export'
        self.post_response_json_key_specifications = [
            {'name': 'csv_bytes', 'null': False}
        ]

        tear_down()
        set_up_permissions()

        self.client_usr_obj = get_or_create_user()
        self.valid_payload = {}

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_with_valid_data(self):
        remove_admin_status()
        payload             = self.valid_payload
        response_content    = self.assert_post_with_valid_payload_is_success(payload=payload)

        ## Check any byte data returned
        self.assertTrue(response_content['post_data']['csv_bytes'] is not None
            ,f"response_content['post_data']['csv_bytes'] should not be null, it should return some byte data in string form")


        grant_admin_status()
        payload             = self.valid_payload
        response_content    = self.assert_post_with_valid_payload_is_success(payload=payload)

        ## For admins, the post_success must be true, and post_msg should be "User is Admin"
        self.assertTrue(response_content['post_data']['csv_bytes'] is not None
            ,f"response_content['post_data']['csv_bytes'] should not be null, it should return some byte data in string form")

    def test_data_validation(self):
        pass ## This api doesn't take in any params


class TestAPIGetCommissionerPMS(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        self.api_name   = 'orgchartportal_get_commissioner_pms'
        self.test_pms   = TEST_COMMISSIONER_PMS
        self.valid_payload = {}
        self.post_response_json_key_specifications = [
            {'name': 'dot_commissioner_pms', 'null': False}
        ]

        tear_down()
        set_up_permissions()

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_with_valid_data(self):
        remove_admin_status()
        payload             = self.valid_payload
        response_content    = self.assert_post_with_valid_payload_is_success(payload=payload)

        ## For normal user, a 7 digit string should be returned as the commissioner pms
        self.assert_post_key_lookup_equivalence(key_name='dot_commissioner_pms', key_value=type(response_content['post_data']['dot_commissioner_pms']), db_value=type(''))
        self.assertTrue(len(response_content['post_data']['dot_commissioner_pms']) == 7
            ,f"response_content['post_data']['dot_commissioner_pms'] is not len 7")
        try:
            test = int(response_content['post_data']['dot_commissioner_pms'])
        except Exception as e:
            self.assertTrue(False
                ,f"response_content['post_data']['dot_commissioner_pms'] is not all digits: {e}")


        grant_admin_status()
        payload             = self.valid_payload
        response_content    = self.assert_post_with_valid_payload_is_success(payload=payload)

        ## For admin, a 7 digit string should be returned as the commissioner pms
        self.assert_post_key_lookup_equivalence(key_name='dot_commissioner_pms', key_value=type(response_content['post_data']['dot_commissioner_pms']), db_value=type(''))
        self.assertTrue(len(response_content['post_data']['dot_commissioner_pms']) == 7
            ,f"response_content['post_data']['dot_commissioner_pms'] is not len 7")
        try:
            test = int(response_content['post_data']['dot_commissioner_pms'])
        except Exception as e:
            self.assertTrue(False
                ,f"response_content['post_data']['dot_commissioner_pms'] is not all digits: {e}")

    def test_data_validation(self):
        pass ## This api doesn't take in any params


class TestAPIOrgChartGetEmpCsv(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        self.api_name   = 'orgchartportal_org_chart_get_emp_csv'
        self.test_pms   = TEST_COMMISSIONER_PMS
        self.valid_payload = {
            'root_pms': self.test_pms
        }
        self.post_response_json_key_specifications = [
            {'name': 'emp_csv', 'null': False}
        ]

        tear_down()
        set_up_permissions()

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_with_valid_data(self):
        remove_admin_status()
        payload             = self.valid_payload
        response_content    = self.assert_post_with_valid_payload_is_success(payload=payload)

        ## For admins, the post_success must be true, and post_msg should be "User is Admin"
        self.assertTrue(response_content['post_data']['emp_csv'] is not None
            ,f"For a normal user, response_content['post_data']['emp_csv'] should not be null, it should return some byte data in string form")

        grant_admin_status()
        payload             = self.valid_payload
        response_content    = self.assert_post_with_valid_payload_is_success(payload=payload)

        ## For admins, the post_success must be true, and post_msg should be "User is Admin"
        self.assertTrue(response_content['post_data']['emp_csv'] is not None
            ,f"For an admin, response_content['post_data']['emp_csv'] should not be null, it should return some byte data in string form")

    def test_data_validation(self):
        payload = self.valid_payload
        parameters = [
            # Parameter name  # Accepted type
            "root_pms"        # str -> string of len 7 with all digits
        ]
        for param_name in parameters:
            if param_name == 'root_pms':
                valid   = [self.test_pms]
                invalid = ['a', 1, 2.3, False, None]
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPIAddUser(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        self.user_obj               = grant_admin_status()
        self.api_name               = 'orgchartportal_add_user'
        self.post_response_json_key_specifications = [
            {'name': 'windows_username' , 'null': False}
            ,{'name': 'pms'             , 'null': False}
            ,{'name': 'is_admin'        , 'null': False}
            ,{'name': 'active'          , 'null': False}
        ]

        self.valid_username         = 'SomeTestUsername'
        self.valid_pms              = TEST_COMMISSIONER_PMS

        self.valid_payloads = [
            {
                'windows_username'  : self.valid_username,
                'pms'               : self.valid_pms,
                'is_admin'          : 'False',
            }
            ,{
                'windows_username'  : self.valid_username,
                'pms'               : self.valid_pms,
                'is_admin'          : 'True',
            }
        ]

    @classmethod
    def tearDownClass(self):
        tear_down()
        self.remove_test_user_if_exists(self)

    def test_api_accept_only_admins(self):
        remove_admin_status()

        payload = self.valid_payloads[0]
        content = self.post_and_get_json_response(payload)

        self.assertTrue((content['post_success']==False) and ("not an admin" in content['post_msg']),
            f"api should have detected that user is not an admin and fail\n{content['post_msg']}")

    def remove_test_user_if_exists(self):
        try:
            new_user = TblUsers.objects.using('OrgChartWrite').get(windows_username__exact=self.valid_username, pms__exact=self.valid_pms)
        except:
            ...#Do nothing
        else:
            new_user.delete(using='OrgChartWrite')

    def test_with_valid_data(self):
        grant_admin_status()

        for payload in self.valid_payloads:
            self.remove_test_user_if_exists()
            self.assert_post_with_valid_payload_is_success(payload=payload)

            ## Check if data was saved correctly
            saved_object = TblUsers.objects.using('OrgChartWrite').get(windows_username__exact=self.valid_username)

            self.assert_post_key_update_equivalence(key_name='windows_username' , key_value=payload['windows_username'] , db_value=saved_object.windows_username)
            self.assert_post_key_update_equivalence(key_name='pms'              , key_value=payload['pms']              , db_value=saved_object.pms)
            self.assert_post_key_update_equivalence(key_name='is_admin'         , key_value=payload['is_admin']         , db_value=str(saved_object.is_admin))
            self.assertTrue(str(saved_object.active)=='True'
                ,f"the newly added user {saved_object.windows_username}'s active field is not True, it must be True. Current value: '{str(saved_object.active)}'")

    def test_data_validation(self):
        grant_admin_status()

        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name    # Accepted type
            "windows_username"  # str -> username
            ,"pms"              # str -> 7 len, all digits
            ,"is_admin"         # str -> 'True' or 'False'
        ]
        for param_name in parameters:
            if param_name == 'windows_username':
                valid   = [self.valid_username]
                invalid = [1, 2.3, False, None]
            elif param_name == 'pms':
                valid   = [self.valid_pms]
                invalid = ['a', 1, 2.3, '-1', '-1.2', '11.567', '2.2', '4.45', None, False, 'a0', '12345678', '123456']
            elif param_name == 'is_admin':
                valid   = ['False', 'True']
                invalid = ['a', 1, 2.3, '-1', '-1.2', '11.567', '2.2', '4.45', None, False]
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.remove_test_user_if_exists()
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.remove_test_user_if_exists()
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPIUpdateUser(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        self.user_obj               = grant_admin_status()
        self.api_name               = 'orgchartportal_update_user'
        self.post_response_json_key_specifications = [
            {'name': 'to_windows_username'  , 'null': False}
            ,{'name': 'column_name'         , 'null': False}
            ,{'name': 'new_value'           , 'null': False}
        ]

        self.valid_payloads = [
            {
                'to_windows_username'   : self.user_obj.windows_username,
                'column_name'           : 'Is Admin',
                'new_value'             : 'True',
            }
            ,{
                'to_windows_username'   : self.user_obj.windows_username,
                'column_name'           : 'Is Admin',
                'new_value'             : 'False',
            }
            ,{
                'to_windows_username'   : self.user_obj.windows_username,
                'column_name'           : 'Active',
                'new_value'             : 'True',
            }
            ,{
                'to_windows_username'   : self.user_obj.windows_username,
                'column_name'           : 'Active',
                'new_value'             : 'False',
            }
        ]

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_api_accept_only_admins(self):
        remove_admin_status()

        payload = self.valid_payloads[0]
        content = self.post_and_get_json_response(payload)

        self.assertTrue((content['post_success']==False) and ("not an admin" in content['post_msg']),
            f"api should have detected that user is not an admin and fail\n{content['post_msg']}")

    def test_with_valid_data(self):
        for payload in self.valid_payloads:
            grant_admin_status()
            self.assert_post_with_valid_payload_is_success(payload=payload)

            ## Check if data was saved correctly
            saved_object = TblUsers.objects.using('OrgChartWrite').get(windows_username__exact=self.user_obj.windows_username)

            if payload['column_name'] == 'Is Admin':
                self.assert_post_key_update_equivalence(key_name=payload['column_name'], key_value=payload['new_value'], db_value=str(saved_object.is_admin))
            elif payload['column_name'] == 'Active':
                self.assert_post_key_update_equivalence(key_name=payload['column_name'], key_value=payload['new_value'], db_value=str(saved_object.active))
            else:
                raise ValueError(f"{payload['column']} is not recognized as a valid column value in the payload")

    def test_data_validation(self):
        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name        # Accepted type
            'to_windows_username'   # str -> windows username
            ,'column_name'          # str -> 'Is Admin' or 'Active' only
            ,'new_value'            # str -> 'True' or 'False' only
        ]
        for param_name in parameters:
            if param_name == 'to_windows_username':
                valid   = [self.user_obj.windows_username]
                invalid = [1, 2.3, False, None, 'sdfds']
            elif param_name == 'column_name':
                valid   = ['Is Admin', 'Active']
                invalid = [1, 2.3, False, None, 'sdfds']
            elif param_name == 'new_value':
                valid   = ['False', 'True']
                invalid = ['a', 1, 2.3, None, False]
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                grant_admin_status()
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                grant_admin_status()
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPIDeleteUser(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        self.api_name               = 'orgchartportal_delete_user'
        self.post_response_json_key_specifications = [
            {'name': 'windows_username'  , 'null': False}
        ]

        self.valid_username         = 'some_random_name'
        self.valid_pms              = TEST_COMMISSIONER_PMS

        self.valid_payloads = [
            {
                'windows_username': self.valid_username,
            }
        ]

    @classmethod
    def tearDownClass(self):
        tear_down()
        try:
            test_user = TblUsers.objects.using('OrgChartWrite').get(windows_username__exact=self.valid_username)
        except ObjectDoesNotExist as e:
            ... ## Good, do nothing
        except:
            raise
        else:
            test_user.delete(using='OrgChartWrite')

    def test_api_accept_only_admins(self):
        remove_admin_status()

        payload = self.valid_payloads[0]
        content = self.post_and_get_json_response(payload)

        self.assertTrue((content['post_success']==False) and ("not an admin" in content['post_msg']),
            f"api should have detected that user is not an admin and fail\n{content['post_msg']}")

    def add_test_user_if_not_exists(self):
        test_user = TblUsers.objects.using('OrgChartWrite').get_or_create(
            windows_username=self.valid_username
            ,pms=TblEmployees.objects.using('OrgChartWrite').get(pms__exact=self.valid_pms)
        )[0]
        test_user.save(using='OrgChartWrite')

    def test_with_valid_data(self):
        for payload in self.valid_payloads:
            grant_admin_status()
            self.add_test_user_if_not_exists()
            response_content = self.assert_post_with_valid_payload_is_success(payload=payload)

            ## Check if data was deleted correctly
            try:
                saved_object = TblUsers.objects.using('OrgChartWrite').get(windows_username__exact=self.valid_username)
            except ObjectDoesNotExist as e:
                ... ## Good, do nothing
            except Exception as e:
                raise ValueError(f"test_with_valid_data(): {e}")
            else:
                self.assertTrue(False, f"{saved_object.windows_username} still exists in the database, unable to delete user")

            ## Check that a string was returned for windows_username
            self.assert_post_key_lookup_equivalence(key_name='windows_username', key_value=response_content['post_data']['windows_username'], db_value=payload['windows_username'])

    def test_data_validation(self):
        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name    # Accepted type
            "windows_username"  # str -> windows username
        ]
        for param_name in parameters:
            if param_name == 'windows_username':
                valid   = [self.valid_username]
                invalid = [1, 2.3, False, None, 'whateverhappened?']
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                grant_admin_status()
                self.add_test_user_if_not_exists()
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                grant_admin_status()
                self.add_test_user_if_not_exists()
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)

