from django.test import Client
import unittest
from .models import *
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.contrib import auth
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import json
from WebAppsMain.settings import TEST_WINDOWS_USERNAME, TEST_PMS, TEST_SUPERVISOR_PMS, DJANGO_DEFINED_GENERIC_LIST_VIEW_CONTEXT_KEYS, DJANGO_DEFINED_GENERIC_DETAIL_VIEW_CONTEXT_KEYS, APP_DEFINED_HTTP_GET_CONTEXT_KEYS
from WebAppsMain.testing_utils import get_to_api, HttpPostTestCase
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


def grant_admin_status(cls=None, windows_username=TEST_WINDOWS_USERNAME):
    """create or get an user and set it up with admin status and return the user object. Defaults to TEST_WINDOWS_USERNAME as the user"""
    try:
        user = get_or_create_user(windows_username=windows_username)
        user.is_admin=True
        user.save(using='OrgChartWrite')
        return user
    except Exception as e:
            raise ValueError(f"grant_admin_status(): {e}")


def remove_admin_status(cls=None, windows_username=TEST_WINDOWS_USERNAME):
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


# Create your tests here.
class TestViewPagesResponse(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        set_up_permissions()
        self.client                 = Client()  ## Required by sub class

        self.remove_admin_status    = remove_admin_status   ## Required by sub class
        self.grant_admin_status     = grant_admin_status    ## Required by sub class

        self.regular_views = [                  ## Required by sub class
            'orgchartportal_home_view',
            'orgchartportal_about_view',
            'orgchartportal_contact_view',
            'orgchartportal_empgrid_view',
            'orgchartportal_orgchart_view',
            'orgchartportal_how_to_use_view',
        ]

        self.admin_views = [                    ## Required by sub class
            'orgchartportal_admin_panel_view',
            'orgchartportal_manage_users_view',
            'orgchartportal_manage_permissions_view',
        ]

        self.additional_context_req = [         ## Required by sub class
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
                ,'qa_fct'                   : self.__assert_empgrid_additional_context_data_quality
            }
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

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_views_response_status_200(self):
        """Test normal user"""
        self.remove_admin_status()
        for view in self.regular_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertEqual(response.status_code, 200, f"'{view}' did not return status code 200")

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertEqual(response.status_code, 200, f"'{view}' did not return status code 200")

        """Test admin user"""
        self.grant_admin_status()
        for view in self.regular_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertEqual(response.status_code, 200, f"'{view}' did not return status code 200")

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertEqual(response.status_code, 200, f"'{view}' did not return status code 200")

    def test_views_response_user_admin_restriction(self):
        """Test normal user, should only have acess to regular views"""
        self.remove_admin_status()
        for view in self.regular_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertTrue(response.context['get_success'], f"'{view}' did not return get_success True on a regular view for a non-admin client\n    {response.context['get_error']}")

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertFalse(response.context['get_success'], f"'{view}' returned get_success True on an admin view for a non-admin client\n    {response.context['get_error']}")
            self.assertTrue("not an Admin" in response.context['get_error'], f"'{view}' did not have error message on an admin view when client is non-admin\n    {response.context['get_error']}")

        """Test admin user, should have access to all views"""
        self.grant_admin_status()
        for view in self.regular_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertTrue(response.context['get_success'], f"'{view}' did not return get_success True on a regular view for an admin client\n    {response.context['get_error']}")

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertTrue(response.context['get_success'], f"'{view}' did not return get_success True on an admin view for an admin client\n    {response.context['get_error']}")

    def __verify_response_with_required_additional_context_data(self, view=None, response=None, view_defined_additional_context_keys=None, additional_context_keys_data_qa_fct=None):
        """
            @view is view name
            @response is the GET response
            @view_defined_additional_context_keys is the list of additional context keys that needs to be in the response
            @additional_context_keys_data_qa_fct will be called if @view_defined_additional_context_keys and itself is not null.
                This is where you can add additional customized assert tests to this function
                Assumes the function is a class function in class SomeTestSuite(unittest.TestCase)
                Will pass self and @response to this fct as the only arguments
                Use it like so:

                    class SomeTestSuite(unittest.TestCase): ## Or another child of unittest.TestCase
                        @classMethod
                        def setUpClass(self):
                            ...
                            self.additional_context_req =   [
                                                                {
                                                                    'view': 'some_view_name'
                                                                    ,'additional_context_keys': ['key_name_1', 'key_name_2', ...]
                                                                    ,'qa_fct': self.__more_qa_asserts      ## Assumes this fct has a reference to self.assertTrue() etc
                                                                }
                                                            ]

                        def __more_qa_asserts(self, response):
                            self.assertTrue(response[...]=True, '...')
                            ...

                        self.test_views_response_data()             ## Implicitly will decode @self.additional_context_req and use it.
        """
        django_default_context_keys = DJANGO_DEFINED_GENERIC_LIST_VIEW_CONTEXT_KEYS + DJANGO_DEFINED_GENERIC_DETAIL_VIEW_CONTEXT_KEYS
        response_context_keys = response.context_data.keys()

        for response_context_key in response_context_keys:
            self.assertTrue( (response_context_key in (view_defined_additional_context_keys + APP_DEFINED_HTTP_GET_CONTEXT_KEYS + django_default_context_keys) ),
                f"{view} response got back a context key that shouldn't exist. Please add this new key to the test suite or change the view: '{response_context_key}'")

        for additional_context_key in view_defined_additional_context_keys:
            self.assertTrue(additional_context_key in response_context_keys,
                f"{view} response is missing this view defined context key '{additional_context_key}'")

        if view_defined_additional_context_keys is not None and additional_context_keys_data_qa_fct is not None:
            additional_context_keys_data_qa_fct(self, response)

    def __assert_empgrid_additional_context_data_quality(self, response):
        ## Make sure the emp_entry_columns_json got all the required fields
        emp_entry_columns_dict  = json.loads(response.context_data['emp_entry_columns_json'])
        fields_api              = set(each['field'] for each in emp_entry_columns_dict)
        fields_base             = set([
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
        if len(fields_api) > len(fields_base):
            raise ValueError(f"orgchartportal_empgrid_view: context variable emp_entry_columns_json got back more fields than expected. These are the unexpected fields: {fields_api - fields_base}")
        self.assertTrue(fields_api == fields_base
            ,f'orgchartportal_empgrid_view: context variable emp_entry_columns_json is missing some fields: {fields_base -  fields_api}')

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

    def __assert_additional_context_data(self, additional_requirements=None):
        """
            @additional_requirements : required, specifies the additional context data for each view and optional its qa assert function.
                It's in this format:
                    [
                        {
                            'view': 'some_view_name'
                            ,'additional_context_keys': ['key_name_1', 'key_name_2', ...]
                            ,'qa_fct': some_unittest_class_fct      ## Assumes this fct has a reference to self.assertTrue() etc
                        }
                    ]
        """
        for view in self.regular_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            if view in [each['view'] for each in additional_requirements]:
                view_additional_req     = next(x for x in additional_requirements if view == x['view'])
                additional_context_keys = view_additional_req['additional_context_keys']
                qa_test                 = view_additional_req['qa_fct']

                self.__verify_response_with_required_additional_context_data(view=view, response=response, view_defined_additional_context_keys=additional_context_keys, additional_context_keys_data_qa_fct=qa_test)
            else:
                ## verify additional context data as [], so that it can detect unrecognized context variable
                self.__verify_response_with_required_additional_context_data(view=view, response=response, view_defined_additional_context_keys=[])

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            if view in [each['view'] for each in additional_requirements]:
                view_additional_req     = next(x for x in additional_requirements if view == x['view'])
                additional_context_keys = view_additional_req['additional_context_keys']
                qa_test                 = view_additional_req['qa_fct']

                self.__verify_response_with_required_additional_context_data(view=view, response=response, view_defined_additional_context_keys=additional_context_keys, additional_context_keys_data_qa_fct=qa_test)
            else:
                ## verify additional context data as [], so that it can detect unrecognized context variable
                self.__verify_response_with_required_additional_context_data(view=view, response=response, view_defined_additional_context_keys=[])

    def test_views_response_data(self):
        """
            Test views to have the required GET request context data
            Some views have additional context data, need to test for those here
        """
        # Test normal user
        self.remove_admin_status()
        self.__assert_additional_context_data(additional_requirements=self.additional_context_req)

        # Test admin user
        self.grant_admin_status()
        self.__assert_additional_context_data(additional_requirements=self.additional_context_req)


class TestAPIUpdateEmployeeData(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        self.api_name   = 'orgchartportal_update_employee_data'
        self.post_response_json_key_specifications = []


        tear_down()
        set_up_permissions()
        get_or_create_user()
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

