from django.test import Client
import unittest
from .models import *
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.contrib import auth
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from WebAppsMain.settings import TEST_WINDOWS_USERNAME, TEST_PMS, DJANGO_DEFINED_GENERIC_LIST_VIEW_CONTEXT_KEYS, DJANGO_DEFINED_GENERIC_DETAIL_VIEW_CONTEXT_KEYS, APP_DEFINED_HTTP_GET_CONTEXT_KEYS
from WebAppsMain.testing_utils import get_to_api, HttpPostTestCase
### DO NOT RUN THIS IN PROD ENVIRONMENT


DEFAULT_WORK_UNIT = '1600'


def get_or_create_user(windows_username=TEST_WINDOWS_USERNAME):
    """create or get an user and return the user object. Defaults to TEST_WINDOWS_USERNAME as the user"""
    try:
        pms = TblEmployees.objects.using('OrgChartWrite').get_or_create(
            pms=TEST_PMS
        )[0]

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


# Create your tests here.
class TestViewPagesResponse(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        set_up_permissions()
        self.client                 = Client()

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

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_views_response_status_200(self):
        """Test normal user"""
        remove_admin_status()
        for view in self.regular_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertEqual(response.status_code, 200, f"'{view}' did not return status code 200")

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertEqual(response.status_code, 200, f"'{view}' did not return status code 200")

        """Test admin user"""
        grant_admin_status()
        for view in self.regular_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertEqual(response.status_code, 200, f"'{view}' did not return status code 200")

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertEqual(response.status_code, 200, f"'{view}' did not return status code 200")

    def test_views_response_user_admin_restriction(self):
        """Test normal user, should only have acess to regular views"""
        remove_admin_status()
        for view in self.regular_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertTrue(response.context['get_success'], f"'{view}' did not return get_success True on a regular view for a non-admin client\n    {response.context['get_error']}")

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertFalse(response.context['get_success'], f"'{view}' returned get_success True on an admin view for a non-admin client\n    {response.context['get_error']}")
            self.assertTrue("not an Admin" in response.context['get_error'], f"'{view}' did not have error message on an admin view when client is non-admin\n    {response.context['get_error']}")

        """Test admin user, should have access to all views"""
        grant_admin_status()
        for view in self.regular_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertTrue(response.context['get_success'], f"'{view}' did not return get_success True on a regular view for an admin client\n    {response.context['get_error']}")

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertTrue(response.context['get_success'], f"'{view}' did not return get_success True on an admin view for an admin client\n    {response.context['get_error']}")

    def __verify_response_with_required_additional_context_data(self, view=None, response=None, view_defined_additional_context_keys=None):
        django_default_context_keys = DJANGO_DEFINED_GENERIC_LIST_VIEW_CONTEXT_KEYS + DJANGO_DEFINED_GENERIC_DETAIL_VIEW_CONTEXT_KEYS
        response_context_keys = response.context_data.keys()

        for response_context_key in response_context_keys:
            self.assertTrue( (response_context_key in (view_defined_additional_context_keys + APP_DEFINED_HTTP_GET_CONTEXT_KEYS + django_default_context_keys) ),
                f"{view} response got back a context key that shouldn't exist. Please add this new key to the test suite or change the view: '{response_context_key}'")

        for additional_context_key in view_defined_additional_context_keys:
            self.assertTrue(additional_context_key in response_context_keys,
                f"{view} response is missing this view defined context key '{additional_context_key}'")

    def __assert_additional_context_data(self):
        for view in self.regular_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            if view == 'orgchartportal_empgrid_view':
                view_defined_additional_context_keys = [
                    'emp_entry_columns_json'
                    ,'emp_entries_json'
                    ,'supervisor_dropdown_list_json'
                    ,'site_dropdown_list_json'
                    ,'site_floor_dropdown_list_json'
                    ,'site_type_dropdown_list_json'
                ]
                self.__verify_response_with_required_additional_context_data(view=view, response=response, view_defined_additional_context_keys=view_defined_additional_context_keys)

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            if view =='orgchartportal_manage_users_view':
                view_defined_additional_context_keys = [
                    'ag_grid_col_def_json'
                    ,'users_data_json'
                ]
                self.__verify_response_with_required_additional_context_data(view=view, response=response, view_defined_additional_context_keys=view_defined_additional_context_keys)
            if view =='orgchartportal_manage_permissions_view':
                view_defined_additional_context_keys = [
                    'ag_grid_col_def_json'
                    ,'permissions_json'
                    ,'user_list'
                    ,'division_list'
                    ,'wu_desc_list'
                ]
                self.__verify_response_with_required_additional_context_data(view=view, response=response, view_defined_additional_context_keys=view_defined_additional_context_keys)

    def test_views_response_data(self):
        """Some views have additional context data, need to test for those here"""
        # Test normal user
        remove_admin_status()
        self.__assert_additional_context_data()

        # Test admin user
        grant_admin_status()
        self.__assert_additional_context_data()
