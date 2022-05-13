from .models import *
from WebAppsMain.settings import TEST_WINDOWS_USERNAME, WEB_APP_NAME_USER_MANAGEMENT
from WebAppsMain.testing_utils import HttpPostTestCase, HttpGetTestCase, grant_membership_admin_status, remove_membership_admin_status, grant_membership_active_status, remove_membership_active_status
from django.core.exceptions import ObjectDoesNotExist
import json

# Create your tests here.


def set_up():
    """Give admin status to @windows_username and make membership active. Defaults to TEST_WINDOWS_USERNAME and WEB_APP_NAME_USER_MANAGEMENT"""
    try:
        grant_membership_admin_status(windows_username=TEST_WINDOWS_USERNAME, web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
        grant_membership_active_status(windows_username=TEST_WINDOWS_USERNAME, web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
    except Exception as e:
        raise ValueError(f"set_up(): {e}")


def tear_down():
    """Removes admin status from @windows_username and make membership inactive. Defaults to TEST_WINDOWS_USERNAME and WEB_APP_NAME_USER_MANAGEMENT"""
    try:
        remove_membership_admin_status(windows_username=TEST_WINDOWS_USERNAME, web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
        remove_membership_active_status(windows_username=TEST_WINDOWS_USERNAME, web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
    except Exception as e:
        raise ValueError(f"tear_down(): {e}")


class TestModelActiveDirectory(HttpGetTestCase):

    def test_must_not_save(self):
        try:
            user_obj = ActiveDirectory.objects.using('default').get(windows_username__exact=TEST_WINDOWS_USERNAME)
            user_obj.first_name = 'hey'
            user_obj.save(using='default')

            ## Test if data actually went through
            user_obj = ActiveDirectory.objects.using('default').get(windows_username__exact=TEST_WINDOWS_USERNAME)
            self.assertTrue(user_obj.first_anme != 'hey'
                ,f"TestModelActiveDirectory: Model cannot allow save(): save() seems to worked")
        except Exception as e:
            if 'This model is immutable.' not in str(e):
                self.assertTrue(False
                    ,f"TestModelActiveDirectory: Model cannot allow save(): {e}")
        else:
            self.assertTrue(False
                ,f"TestModelActiveDirectory: Model cannot allow save()")

    def test_must_not_delete(self):
        try:
            user_obj = ActiveDirectory.objects.using('default').get(windows_username__exact=TEST_WINDOWS_USERNAME)
            user_obj.delete(using='default')

            ## Test if data actually went through
            try:
                user_obj = ActiveDirectory.objects.using('default').get(windows_username__exact=TEST_WINDOWS_USERNAME)
            except ObjectDoesNotExist:
                self.assertTrue(False
                    ,f"TestModelActiveDirectory: Model cannot allow delete(): delete() seems to worked")
            else:
                pass ## Good! delete() didn't work!
        except Exception as e:
            if 'This model is immutable.' not in str(e):
                self.assertTrue(False
                    ,f"TestModelActiveDirectory: Model cannot allow delete(): {e}")
        else:
            self.assertTrue(False
                ,f"TestModelActiveDirectory: Model cannot allow delete()")

    def test_must_not_create(self):
        try:
            user_obj = ActiveDirectory.objects.using('default').create(
                object_guid='abc123'
                ,sid='abc1234'
                ,windows_username='abc'
                ,pms='1234567'
                ,object_class='asd'
                ,enabled=True
                ,first_name='first_n'
                ,last_name='last_n'
                ,full_name='full_n'
                ,dot_email='fn_ln@gmail.com'
            )

            ## Test if data actually went through
            try:
                user_obj = ActiveDirectory.objects.using('default').get(windows_username__exact='abc')
            except ObjectDoesNotExist:
                pass ## Good! create() didn't work!
            else:
                self.assertTrue(False
                    ,f"TestModelActiveDirectory: Model cannot allow create(): create() seems to worked")
        except Exception as e:
            if 'This model is immutable.' not in str(e):
                self.assertTrue(False
                    ,f"TestModelActiveDirectory: Model cannot allow create(): {e}")
        else:
            self.assertTrue(False
                ,f"TestModelActiveDirectory: Model cannot allow create()")

    def test_must_not_update(self):
        try:
            user_obj = ActiveDirectory.objects.using('default').get(windows_username__exact=TEST_WINDOWS_USERNAME)
            user_obj.update(full_name='some full name')

            ## Test if data actually went through
            user_obj = ActiveDirectory.objects.using('default').get(windows_username__exact=TEST_WINDOWS_USERNAME)
            self.assertTrue(user_obj.full_name != 'some full name'
                ,f"TestModelActiveDirectory: Model cannot allow update(): update() seems to worked")
        except Exception as e:
            if 'This model is immutable.' not in str(e):
                self.assertTrue(False
                    ,f"TestModelActiveDirectory: Model cannot allow update(): {e}")
        else:
            self.assertTrue(False
                ,f"TestModelActiveDirectory: Model cannot allow update()")


class TestViewPagesResponse(HttpGetTestCase):
    @classmethod
    def setUpClass(self):
        set_up()

        self.regular_views = [
            'usermanagement_home_view',
            'usermanagement_about_view',
            'usermanagement_contact_view',
        ]

        self.admin_views = [
            'usermanagement_manage_web_apps_view',
        ]

        self.additional_context_requirements = [
            ## The below are admin views
            {
                'view'                      : 'usermanagement_manage_web_apps_view'
                ,'additional_context_keys'  : [
                                                'ag_grid_col_def_json'
                                                ,'rows_data_json'
                                            ]
                ,'qa_fct'                   : self.__assert_additional_context_qa_manage_web_apps
            }
        ]

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_views_response_status_200(self):
        """Test normal user"""
        remove_membership_admin_status(web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
        self.assert_response_status_200()

        """Test admin user"""
        grant_membership_admin_status(web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
        self.assert_response_status_200()

    def test_views_response_user_admin_restriction(self):
        """Test inactive user webapp membership (Non-Admin), should have NO access to regular or admin views"""
        remove_membership_admin_status(web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
        remove_membership_active_status(web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
        self.assert_inactive_user_no_access_on_normal_and_admin_view()

        """Test inactive user webapp membership (Admin), should have NO access to regular or admin views"""
        grant_membership_admin_status(web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
        remove_membership_active_status(web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
        self.assert_inactive_user_no_access_on_normal_and_admin_view()

        """Test active user webapp membership (Non-Admin), should only have access to regular views"""
        grant_membership_active_status(web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
        remove_membership_admin_status(web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
        self.assert_user_access_on_normal_and_admin_view()

        """Test active user webapp membership (Admin), should have access to regular and admin views"""
        grant_membership_active_status(web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
        grant_membership_admin_status(web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
        self.assert_admin_access_on_normal_and_admin_view()

    def test_views_response_data(self):
        """
            Test views to have the required GET request context data
            Some views have additional context data, need to test for those here
        """
        # Test normal user
        remove_membership_admin_status(web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
        self.assert_additional_context_data(additional_requirements=self.additional_context_requirements)

        # Test admin user
        grant_membership_admin_status(web_app_name=WEB_APP_NAME_USER_MANAGEMENT)
        self.assert_additional_context_data(additional_requirements=self.additional_context_requirements)

    def __assert_additional_context_qa_manage_web_apps(self, response):
        ## Make sure the ag_grid_col_def_json got all the required fields
        ag_grid_col_def_dict    = json.loads(response.context_data['ag_grid_col_def_json'])
        from_api_fields         = set(each['field'] for each in ag_grid_col_def_dict)
        required_fields         = set([
            'web_app_id'
            ,'web_app_name'
            ,'is_active'
        ])
        if len(from_api_fields) > len(required_fields):
            raise ValueError(f"usermanagement_manage_web_apps_view: context variable ag_grid_col_def_json got back more fields than expected. These are the unexpected fields: {from_api_fields - required_fields}")
        self.assertTrue(from_api_fields == required_fields
            ,f'usermanagement_manage_web_apps_view: context variable ag_grid_col_def_json is missing some fields: {required_fields -  from_api_fields}')

        ## Make sure rows_data_json has at least the app name of the UserManagement web app that we are testing
        row_data = json.loads(response.context_data['rows_data_json'])
        self.assertTrue(len(row_data) > 0
            ,f"usermanagement_manage_web_apps_view: context variable rows_data_json doesn't have any data")
        self.assertTrue(sorted(required_fields) == sorted(row_data[0].keys())
            ,f'usermanagement_manage_web_apps_view: context variable rows_data_json is missing some fields: {required_fields -  set(row_data[0].keys())}')

