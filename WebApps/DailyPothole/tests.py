from django.test import Client
import unittest
from .models import *
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.contrib import auth
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from WebAppsMain.settings import TEST_WINDOWS_USERNAME, DJANGO_DEFINED_GENERIC_LIST_VIEW_CONTEXT_KEYS, DJANGO_DEFINED_GENERIC_DETAIL_VIEW_CONTEXT_KEYS, APP_DEFINED_HTTP_GET_CONTEXT_KEYS
from WebAppsMain.testing_utils import get_to_api, HttpPostTestCase
### DO NOT RUN THIS IN PROD ENVIRONMENT


DEFAULT_OPERATION = "BRIDGE PM"
DEFAULT_BORO = "QUEENS"


def get_or_create_user(windows_username=TEST_WINDOWS_USERNAME):
    """create or get an user and return the user object. Defaults to TEST_WINDOWS_USERNAME as the user"""
    try:
        return TblUser.objects.using('DailyPothole').get_or_create(
            username=windows_username
        )[0]
    except Exception as e:
        raise ValueError(f"get_or_create_user(): {e}")


def grant_admin_status(windows_username=TEST_WINDOWS_USERNAME):
    """create or get an user and set it up with admin status and return the user object. Defaults to TEST_WINDOWS_USERNAME as the user"""
    try:
        user = get_or_create_user(windows_username=windows_username)
        user.is_admin=True
        user.save(using='DailyPothole')
        return user
    except Exception as e:
            raise ValueError(f"grant_admin_status(): {e}")


def remove_admin_status(windows_username=TEST_WINDOWS_USERNAME):
    """removes the admin status of an user"""
    try:
        user = get_or_create_user(windows_username=windows_username)
        user.is_admin=False
        user.save(using='DailyPothole')
        return user
    except Exception as e:
            raise ValueError(f"remove_admin_status(): {e}")


def set_up_permissions(windows_username=TEST_WINDOWS_USERNAME, operation_boro_pairs=[(DEFAULT_OPERATION, DEFAULT_BORO)]):
    """
        set up permissions for a user. If user is admin, the permissions added will probably mean nothing.

        @windows_username is self explanatory, just one name
        @operation_boro_pairs should be a list of 2-item tuple like this: (str_operation, str_boro)
    """
    try:
        for each in operation_boro_pairs:
            operation   = each[0]
            boro        = each[1]

            operation_boro = TblOperationBoro.objects.using('DailyPothole').get(
                operation_id__operation__exact  = operation
                ,boro_id__boro_long__exact      = boro
                ,is_active                      = True
            )

            user = get_or_create_user(windows_username=windows_username)
            permission = TblPermission.objects.using('DailyPothole').get_or_create(
                user_id             = user
                ,operation_boro_id  = operation_boro
            )[0]
            permission.is_active = True
            permission.save(using="DailyPothole")

    except Exception as e:
        raise ValueError(f"set_up_permissions(): {e}")


def tear_down_permissions(windows_username=TEST_WINDOWS_USERNAME):
    """remove all permissions for an user. If user is admin, the permissions removed will probably mean nothing."""
    try:
        permissions = TblPermission.objects.using('DailyPothole').filter(
            user_id__username__exact=windows_username
        )

        for each in permissions:
            each.delete(using='DailyPothole')
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
            'dailypothole_home_view',
            'dailypothole_about_view',
            'dailypothole_contact_view',
            'dailypothole_pothole_data_entry_view',
        ]

        self.admin_views = [
            'dailypothole_pothole_data_grid_view',
            'dailypothole_complaints_input_view',
            'dailypothole_reports_view',
            'dailypothole_admin_panel_view',
            'dailypothole_users_panel_view',
            'dailypothole_user_permissions_panel_view',
            'dailypothole_csv_export_view',
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
            if view == 'dailypothole_pothole_data_entry_view':
                view_defined_additional_context_keys = [
                    'today'
                    ,'operation_boro_permissions'
                ]
                self.__verify_response_with_required_additional_context_data(view=view, response=response, view_defined_additional_context_keys=view_defined_additional_context_keys)

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            if view == 'dailypothole_pothole_data_grid_view':
                view_defined_additional_context_keys = [
                    'ag_grid_col_def_json'
                    ,'pothole_data_json'
                ]
                self.__verify_response_with_required_additional_context_data(view=view, response=response, view_defined_additional_context_keys=view_defined_additional_context_keys)
            if view == 'dailypothole_csv_export_view':
                view_defined_additional_context_keys = [
                    'operation_list'
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


class TestAPIUpdatePotholesData(HttpPostTestCase):
    """methods that starts with name 'test...' are the methods be called by unittest"""
    @classmethod
    def setUpClass(self):
        tear_down()
        set_up_permissions()
        self.user_obj                   = get_or_create_user()
        self.api_name                   = 'dailypothole_update_potholes_data_api'
        self.post_response_json_key_specifications = []

        self.valid_operation            = DEFAULT_OPERATION
        self.valid_borough              = DEFAULT_BORO
        self.valid_date                 = f'{datetime.now().strftime("%Y-%m-%d")}'
        self.valid_crew_count           = 1
        self.valid_holes_repaired       = 2
        self.valid_planned_crew_count   = 3

        self.valid_payload = {
            'PotholeData': {   ## valid for Pothole Data request
                'request_type'              : 'PotholeData',
                'date_of_repair'            : self.valid_date,
                'operation'                 : self.valid_operation,
                'borough'                   : self.valid_borough,
                'crew_count'                : self.valid_crew_count,
                'holes_repaired'            : self.valid_holes_repaired,
                'planned_crew_count'        : None,
                'planned_date'              : None,
            }
            ,'TodayCrewData': {  ## valid for Today Crew Data request
                "request_type"              : 'TodayCrewData',
                "date_of_repair"            : None,
                "operation"                 : self.valid_operation,
                "borough"                   : self.valid_borough,
                "crew_count"                : None,
                "holes_repaired"            : None,
                "planned_crew_count"        : self.valid_planned_crew_count,
                "planned_date"              : self.valid_date,
            }
        }

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_with_valid_data(self):
        for payload_type in self.valid_payload:
            payload = self.valid_payload[payload_type]
            response_content = self.post_and_get_json_response(payload)

            ## Check that the request was successful
            self.assertEqual(response_content['post_success'], True,
                f"payload_type '{payload_type}': api call was not successfully with valid data\n{response_content['post_msg']}")

            ## Check that the returned JSON Response got all the data it required
            self.assert_response_satisfy_param_requirements(response_content=response_content)

            ## Check if data was saved correctly
            saved_object = TblPotholeMaster.objects.using('DailyPothole').get(
                repair_date=self.valid_date
                ,operation_boro_id__operation_id__operation__exact=self.valid_operation
                ,operation_boro_id__boro_id__boro_long__exact=self.valid_borough
            )

            if payload_type == 'PotholeData':
                self.assert_post_key_update_equivalence(key_name=f'{payload_type}: [repair_crew_count]', key_value=float(self.valid_crew_count)    , db_value=float(saved_object.repair_crew_count))
                self.assert_post_key_update_equivalence(key_name=f'{payload_type}: [repair_crew_count]', key_value=float(self.valid_holes_repaired), db_value=float(saved_object.holes_repaired))
            elif payload_type == 'TodayCrewData':
                self.assert_post_key_update_equivalence(key_name=f'{payload_type}: [daily_crew_count]', key_value=float(self.valid_planned_crew_count), db_value=float(saved_object.daily_crew_count))
            else:
                raise ValueError( f"TestAPIUpdatePotholesData: test_with_valid_data(): payload_type not recognized in test case: '{payload_type}'" )

            self.assertTrue(  (timezone.now() - saved_object.last_modified_timestamp).total_seconds() < 10,
                f"payload_type '{payload_type}': [last_modified_timestamp] didn't save correctly: '{saved_object.last_modified_timestamp.strftime('%Y-%m-%d %H:%M:%S')}' input-->database '{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}'. Cannot exceed more than 10 seconds difference" )
            self.assert_post_key_update_equivalence(key_name=f"{payload_type}: [last_modified_by_user_id]", key_value=self.user_obj.user_id, db_value=saved_object.last_modified_by_user_id.user_id)

    def test_data_validation(self):
        f"""Testing {self.api_name} data validation"""

        ## For PotholeData
        payload = self.valid_payload['PotholeData']
        parameters = [
            # Parameter name    # Accepted type
            "request_type"      # str   -> ['PotholeData']
            ,"operation"        # str   -> 'operation_names'
            ,"borough"          # str   -> 'boro_names'
            ,"date_of_repair"   # str   -> 'YYYY-MM-DD'
            ,"crew_count"       # float -> >= 0
            ,"holes_repaired"   # int   -> >= 0
        ]
        for param_name in parameters:

            if param_name == 'request_type':
                valid   = ['PotholeData']
                invalid = ['a', 1, 2.3, None, True]
            elif param_name == 'operation':
                valid   = [self.valid_operation]
                invalid = ['a', 1, 2.3, None, False]
            elif param_name == 'borough':
                valid   = [self.valid_borough]
                invalid = ['a', 1, 2.3, None, False]
            elif param_name == 'date_of_repair':
                valid   = [f'{datetime.now().strftime("%Y-%m-%d")}']
                invalid = ['a', 1, 2.3, False]
            elif param_name == 'crew_count':
                valid   = [1, 1.2]
                invalid = ['a', -5, False]
            elif param_name == 'holes_repaired':
                valid   = [1]
                invalid = ['a', -5, 2.4, False]
            else:
                raise ValueError(f"test_data_validation(): PotholeData -> parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


        ## For TodayCrewData
        payload = self.valid_payload['TodayCrewData']
        parameters = [
            "request_type"          # str   -> ['TodayCrewData']
            ,"operation"            # str   -> 'operation_names'
            ,"borough"              # str   -> 'boro_names'
            ,"planned_date"         # str   -> 'YYYY-MM-DD'
            ,"planned_crew_count"   # float -> >= 0
        ]
        for param_name in parameters:

            if param_name == 'request_type':
                valid   = ['TodayCrewData']
                invalid = ['a', 1, 2.3, None, True]
            elif param_name == 'operation':
                valid   = [self.valid_operation]
                invalid = ['a', 1, 2.3, None, False]
            elif param_name == 'borough':
                valid   = [self.valid_borough]
                invalid = ['a', 1, 2.3, None, False]
            elif param_name == 'planned_date':
                valid   = [f'{datetime.now().strftime("%Y-%m-%d")}']
                invalid = ['a', 1, 2.3, False]
            elif param_name == 'planned_crew_count':
                valid   = [1, 1.2]
                invalid = ['a', -5, False]
            else:
                raise ValueError(f"test_data_validation(): TodayCrewData -> parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPILookupPotholesAndCrewData(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        set_up_permissions()
        self.api_name               = 'dailypothole_lookup_potholes_and_crew_data_api'
        self.post_response_json_key_specifications = [
            {'name': 'look_up_date'         , 'null': False}
            ,{'name': 'repair_crew_count'   , 'null': True}
            ,{'name': 'holes_repaired'      , 'null': True}
            ,{'name': 'daily_crew_count'    , 'null': True}
        ]

        self.valid_look_up_date     = f'{datetime.now().strftime("%Y-%m-%d")}'
        self.valid_operation        = DEFAULT_OPERATION
        self.valid_borough          = DEFAULT_BORO

        self.valid_payload = {
            'look_up_date'  : self.valid_look_up_date,
            'operation'     : self.valid_operation,
            'borough'       : self.valid_borough,
        }

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_with_valid_data(self):
        payload = self.valid_payload
        response_content = self.post_and_get_json_response( payload )

        ## Check that the request was successful
        self.assertEqual(response_content['post_success'], True,
            f"api call was not successfully with valid data")

        ## Check that the returned JSON Response got all the data it required
        self.assert_response_satisfy_param_requirements(response_content=response_content)

        ## Check if data was queried correctly
        lookup_object = TblPotholeMaster.objects.using('DailyPothole').get(
            repair_date__exact=payload['look_up_date']
            ,operation_boro_id__operation_id__operation__exact=payload['operation']
            ,operation_boro_id__boro_id__boro_long__exact=payload['borough']
        )
        self.assert_post_key_lookup_equivalence(key_name='look_up_date'     , key_value=response_content['post_data']['look_up_date']        , db_value=lookup_object.repair_date)
        self.assert_post_key_lookup_equivalence(key_name='repair_crew_count', key_value=response_content['post_data']['repair_crew_count']   , db_value=lookup_object.repair_crew_count)
        self.assert_post_key_lookup_equivalence(key_name='holes_repaired'   , key_value=response_content['post_data']['holes_repaired']      , db_value=lookup_object.holes_repaired)
        self.assert_post_key_lookup_equivalence(key_name='daily_crew_count' , key_value=response_content['post_data']['daily_crew_count']    , db_value=lookup_object.daily_crew_count)

    def test_data_validation(self):
        payload = self.valid_payload
        parameters = [
            # Parameter name    # Accepted type
            "look_up_date"      # str   -> 'YYYY-MM-DD'
            ,"operation"        # str   -> 'operation_names'
            ,"borough"          # str   -> 'boro_names'
        ]
        for param_name in parameters:

            if param_name == 'look_up_date':
                valid   = [f'{datetime.now().strftime("%Y-%m-%d")}']
                invalid = ['a', 1, 2.3, False]
            elif param_name == 'operation':
                valid   = [self.valid_operation]
                invalid = ['a', 1, 2.3, None, False]
            elif param_name == 'borough':
                valid   = [self.valid_borough]
                invalid = ['a', 1, 2.3, None, False]
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPIUpdatePotholesFromDataGrid(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        self.user_obj               = grant_admin_status()
        self.api_name               = 'dailypothole_update_potholes_from_data_grid_api'
        self.post_response_json_key_specifications = [
            {'name': 'repair_date'  , 'null': False}
            ,{'name': 'operation'   , 'null': False}
            ,{'name': 'boro_long'   , 'null': False}
            ,{'name': 'column_name' , 'null': False}
            ,{'name': 'new_value'   , 'null': False}
            ,{'name': 'updated_by'  , 'null': False}
        ]

        self.valid_repair_date      = f'{datetime.now().strftime("%Y-%m-%d")}'
        self.valid_operation        = DEFAULT_OPERATION
        self.valid_boro_long        = DEFAULT_BORO

        self.valid_payloads = [
            {
                'repair_date'   : self.valid_repair_date,
                'operation'     : self.valid_operation,
                'boro_long'     : self.valid_boro_long,
                'column_name'   : 'Repair Crew Count',
                'new_value'     : '10.2',
            }
            ,{
                'repair_date'   : self.valid_repair_date,
                'operation'     : self.valid_operation,
                'boro_long'     : self.valid_boro_long,
                'column_name'   : 'Holes Repaired',
                'new_value'     : '20',
            }
            ,{
                'repair_date'   : self.valid_repair_date,
                'operation'     : self.valid_operation,
                'boro_long'     : self.valid_boro_long,
                'column_name'   : 'Daily Crew Count',
                'new_value'     : '30.2',
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
            f"api should have detected that user is not an admin and fail")

    def test_with_valid_data(self):
        grant_admin_status()
        for payload in self.valid_payloads:
            response_content = self.post_and_get_json_response( payload )

            ## Check that the request was successful
            self.assertTrue(response_content['post_success'],
                f"api call was not successfully with valid data: {response_content['post_msg']}")

            ## Check that the returned JSON Response got all the data it required
            self.assert_response_satisfy_param_requirements(response_content=response_content)

            ## Check if data was saved correctly
            saved_object = TblPotholeMaster.objects.using('DailyPothole').get(
                repair_date=self.valid_repair_date
                ,operation_boro_id__operation_id__operation__exact=self.valid_operation
                ,operation_boro_id__boro_id__boro_long__exact=self.valid_boro_long
            )

            if payload['column_name'] == 'Repair Crew Count':
                self.assert_post_key_update_equivalence(key_name=f"{payload['column_name']}: [repair_crew_count]", key_value=float(payload['new_value']), db_value=float(saved_object.repair_crew_count))
            elif payload['column_name'] == 'Holes Repaired':
                self.assert_post_key_update_equivalence(key_name=f"{payload['column_name']}: [holes_repaired]", key_value=float(payload['new_value']), db_value=float(saved_object.holes_repaired))
            elif payload['column_name'] == 'Daily Crew Count':
                self.assert_post_key_update_equivalence(key_name=f"{payload['column_name']}: [daily_crew_count]", key_value=float(payload['new_value']), db_value=float(saved_object.daily_crew_count))
            else:
                raise ValueError( f"TestAPIUpdatePotholesFromDataGrid: test_with_valid_data(): payload['column_name'] not recognized in test case: '{payload['column_name']}'" )

            self.assertTrue(  (timezone.now() - saved_object.last_modified_timestamp).total_seconds() < 10,
                f"payload['column_name'] '{payload['column_name']}': [last_modified_timestamp] didn't save correctly: '{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}' input-->database '{saved_object.last_modified_timestamp.strftime('%Y-%m-%d %H:%M:%S')}'. Cannot exceed more than 10 seconds difference" )
            self.assert_post_key_update_equivalence(key_name=f"{payload['column_name']}: [last_modified_by_user_id]", key_value=self.user_obj.user_id, db_value=saved_object.last_modified_by_user_id.user_id)

    def test_data_validation(self):
        grant_admin_status()
        crew_count_payload      = self.valid_payloads[0]
        holes_repaired_payload  = self.valid_payloads[1]
        parameters = [
            # Parameter name    # Accepted type
            "repair_date"       # str   -> 'YYYY-MM-DD'
            ,"operation"        # str   -> 'operation_names'
            ,"boro_long"        # str   -> 'boro_names'
            ,"column_name"      # str   -> ['Repair Crew Count', 'Holes Repaired', 'Daily Crew Count']
            ,"new_value"        # str   -> string formatted postive int(for holes repaired) or string formatted decimal(no more than 2 decimal places, for crew count).
        ]
        for param_name in parameters:

            ## Test the two crew counts which allows positive decimal and int
            if param_name == 'repair_date':
                valid   = [f'{datetime.now().strftime("%Y-%m-%d")}']
                invalid = ['a', 1, 2.3, False]
            elif param_name == 'operation':
                valid   = [self.valid_operation]
                invalid = ['a', 1, 2.3, None, False]
            elif param_name == 'boro_long':
                valid   = [self.valid_boro_long]
                invalid = ['a', 1, 2.3, None, False]
            elif param_name == 'column_name':
                valid   = ['Repair Crew Count', 'Daily Crew Count']
                invalid = ['a', 1, 2.3, None, False]
            elif param_name == 'new_value':
                valid   = ['0', '1', '2.2', '4.45']
                invalid = ['a', 1, 2.3, '-1', '-1.2', '11.567', None, False]
            else:
                raise ValueError(f"test_data_validation(): Crew Count -> parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=crew_count_payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=crew_count_payload, testing_param_name=param_name, testing_data=data)

            ## Test the holes repaired which allows only positive int
            if param_name == 'repair_date':
                valid   = [f'{datetime.now().strftime("%Y-%m-%d")}']
                invalid = ['a', 1, 2.3, False]
            elif param_name == 'operation':
                valid   = [self.valid_operation]
                invalid = ['a', 1, 2.3, None, False]
            elif param_name == 'boro_long':
                valid   = [self.valid_boro_long]
                invalid = ['a', 1, 2.3, None, False]
            elif param_name == 'column_name':
                valid   = ['Holes Repaired']
                invalid = ['a', 1, 2.3, None, False]
            elif param_name == 'new_value':
                valid   = ['0', '1']
                invalid = ['a', 1, 2.3, '-1', '-1.2', '11.567', '2.2', '4.45', None, False]
            else:
                raise ValueError(f"test_data_validation(): Holes Repaired -> parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=holes_repaired_payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=holes_repaired_payload, testing_param_name=param_name, testing_data=data)


class TestAPIUpdateComplaintsData(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        self.user_obj               = grant_admin_status()
        self.api_name               = 'dailypothole_update_complaints_data_api'
        self.post_response_json_key_specifications = [
            {'name': 'complaint_date'       , 'null': False}
            ,{'name': 'fits_bronx'          , 'null': False}
            ,{'name': 'fits_brooklyn'       , 'null': False}
            ,{'name': 'fits_manhattan'      , 'null': False}
            ,{'name': 'fits_queens'         , 'null': False}
            ,{'name': 'fits_staten_island'  , 'null': False}
            ,{'name': 'fits_unassigned'     , 'null': False}
            ,{'name': 'open_siebel'         , 'null': False}
        ]

        self.valid_complaint_date         = f'{datetime.now().strftime("%Y-%m-%d")}'
        self.valid_fits_bronx             = '1'
        self.valid_fits_brooklyn          = '2'
        self.valid_fits_manhattan         = '3'
        self.valid_fits_queens            = '4'
        self.valid_fits_staten_island     = '5'
        self.valid_fits_unassigned        = '6'
        self.valid_open_siebel            = '7'

        self.valid_payloads = [
            {
                'complaint_date'    : self.valid_complaint_date,
                'fits_bronx'        : self.valid_fits_bronx,
                'fits_brooklyn'     : self.valid_fits_brooklyn,
                'fits_manhattan'    : self.valid_fits_manhattan,
                'fits_queens'       : self.valid_fits_queens,
                'fits_staten_island': self.valid_fits_staten_island,
                'fits_unassigned'   : self.valid_fits_unassigned,
                'open_siebel'       : self.valid_open_siebel
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
        grant_admin_status()
        for payload in self.valid_payloads:
            response_content = self.post_and_get_json_response( payload )

            ## Check that the request was successful
            self.assertTrue(response_content['post_success'],
                f"api call was not successfully with valid data: {response_content['post_msg']}")

            ## Check that the returned JSON Response got all the data it required

            self.assert_response_satisfy_param_requirements(response_content=response_content)

            ## Check if data was saved correctly
            saved_object = TblComplaint.objects.using('DailyPothole').get(
                complaint_date__exact=payload['complaint_date'],
            )

            self.assert_post_key_update_equivalence(key_name='fits_bronx'           , key_value=int(payload['fits_bronx'])         , db_value=saved_object.fits_bronx)
            self.assert_post_key_update_equivalence(key_name='fits_brooklyn'        , key_value=int(payload['fits_brooklyn'])      , db_value=saved_object.fits_brooklyn)
            self.assert_post_key_update_equivalence(key_name='fits_manhattan'       , key_value=int(payload['fits_manhattan'])     , db_value=saved_object.fits_manhattan)
            self.assert_post_key_update_equivalence(key_name='fits_queens'          , key_value=int(payload['fits_queens'])        , db_value=saved_object.fits_queens)
            self.assert_post_key_update_equivalence(key_name='fits_staten_island'   , key_value=int(payload['fits_staten_island']) , db_value=saved_object.fits_staten_island)
            self.assert_post_key_update_equivalence(key_name='fits_unassigned'      , key_value=int(payload['fits_unassigned'])    , db_value=saved_object.fits_unassigned)
            self.assert_post_key_update_equivalence(key_name='siebel_complaints'    , key_value=int(payload['open_siebel'])        , db_value=saved_object.siebel_complaints)

    def test_data_validation(self):
        grant_admin_status()
        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name        # Accepted type
            "complaint_date"        # str -> 'YYYY-MM-DD'
            ,"fits_bronx"           # str -> string formatted positive int
            ,"fits_brooklyn"        # str -> string formatted positive int
            ,"fits_manhattan"       # str -> string formatted positive int
            ,"fits_queens"          # str -> string formatted positive int
            ,"fits_staten_island"   # str -> string formatted positive int
            ,"fits_unassigned"      # str -> string formatted positive int
            ,"open_siebel"          # str -> string formatted positive int
        ]
        for param_name in parameters:
            if param_name == 'complaint_date':
                valid   = [f'{datetime.now().strftime("%Y-%m-%d")}']
                invalid = ['a', 1, 2.3, False]
            elif param_name in ['fits_bronx', 'fits_brooklyn', 'fits_manhattan', 'fits_queens', 'fits_staten_island', 'fits_unassigned', 'open_siebel']:
                valid   = ['0', '1']
                invalid = ['a', 1, 2.3, '-1', '-1.2', '11.567', '2.2', '4.45', None, False]
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPILookupComplaintsData(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        self.api_name                   = 'dailypothole_lookup_complaints_data_api'
        self.post_response_json_key_specifications = [
            {'name': 'complaint_date'       , 'null': False}
            ,{'name': 'fits_bronx'          , 'null': False}
            ,{'name': 'fits_brooklyn'       , 'null': False}
            ,{'name': 'fits_manhattan'      , 'null': False}
            ,{'name': 'fits_queens'         , 'null': False}
            ,{'name': 'fits_staten_island'  , 'null': False}
            ,{'name': 'fits_unassigned'     , 'null': False}
            ,{'name': 'open_siebel'         , 'null': True}
        ]

        self.valid_complaint_date       = f'{datetime.now().strftime("%Y-%m-%d")}'

        self.valid_payloads = [
            {
                'complaint_date'    : self.valid_complaint_date,
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

    def set_up_test_data(self):
        complaint_data = TblComplaint.objects.using('DailyPothole').get(
            complaint_date__exact=self.valid_complaint_date,
        )

        complaint_data.fits_bronx         = 401
        complaint_data.fits_brooklyn      = 402
        complaint_data.fits_manhattan     = 403
        complaint_data.fits_queens        = 404
        complaint_data.fits_staten_island = 405
        complaint_data.fits_unassigned    = 406
        complaint_data.siebel_complaints  = None
        complaint_data.save(using='DailyPothole')

    def test_with_valid_data(self):
        self.set_up_test_data()
        grant_admin_status()

        for payload in self.valid_payloads:
            response_content = self.post_and_get_json_response( payload )

            ## Check that the request was successful
            self.assertTrue(response_content['post_success'],
                f"api call was not successfully with valid data: {response_content['post_msg']}")

            ## Check that the returned JSON Response got all the data it required
            self.assert_response_satisfy_param_requirements(response_content=response_content)

            ## Check if data was queried correctly
            lookup_object = TblComplaint.objects.using('DailyPothole').get(
                complaint_date__exact=payload['complaint_date']
            )
            self.assert_post_key_lookup_equivalence(key_name='complaint_date'       , key_value=response_content['post_data']['complaint_date']     , db_value=lookup_object.complaint_date)
            self.assert_post_key_lookup_equivalence(key_name='fits_bronx'           , key_value=response_content['post_data']['fits_bronx']         , db_value=lookup_object.fits_bronx)
            self.assert_post_key_lookup_equivalence(key_name='fits_brooklyn'        , key_value=response_content['post_data']['fits_brooklyn']      , db_value=lookup_object.fits_brooklyn)
            self.assert_post_key_lookup_equivalence(key_name='fits_manhattan'       , key_value=response_content['post_data']['fits_manhattan']     , db_value=lookup_object.fits_manhattan)
            self.assert_post_key_lookup_equivalence(key_name='fits_queens'          , key_value=response_content['post_data']['fits_queens']        , db_value=lookup_object.fits_queens)
            self.assert_post_key_lookup_equivalence(key_name='fits_staten_island'   , key_value=response_content['post_data']['fits_staten_island'] , db_value=lookup_object.fits_staten_island)
            self.assert_post_key_lookup_equivalence(key_name='fits_unassigned'      , key_value=response_content['post_data']['fits_unassigned']    , db_value=lookup_object.fits_unassigned)
            self.assert_post_key_lookup_equivalence(key_name='open_siebel'          , key_value=response_content['post_data']['open_siebel']        , db_value=lookup_object.siebel_complaints)

    def test_data_validation(self):
        self.set_up_test_data()
        grant_admin_status()

        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name        # Accepted type
            "complaint_date"        # str -> 'YYYY-MM-DD'
        ]
        for param_name in parameters:
            if param_name == 'complaint_date':
                valid   = [f'{datetime.now().strftime("%Y-%m-%d")}']
                invalid = ['a', 1, 2.3, False, None]
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPIGetPDFReport(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        self.api_name           = 'dailypothole_get_pdf_report_api'
        self.post_response_json_key_specifications = [
            {'name': 'pdf_bytes'       , 'null': False}
        ]

        self.valid_report_date  = f'{datetime.now().strftime("%Y-%m-%d")}'

        self.valid_payloads = [
            {
                'report_date'    : self.valid_report_date,
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
        grant_admin_status()
        for payload in self.valid_payloads:
            response_content = self.post_and_get_json_response( payload )

            ## Check that the request was successful
            self.assertTrue(response_content['post_success'],
                f"api call was not successfully with valid data: {response_content['post_msg']}")

            ## Check that the returned JSON Response got all the data it required
            self.assert_response_satisfy_param_requirements(response_content=response_content)

    def test_data_validation(self):
        grant_admin_status()
        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name    # Accepted type
            "report_date"       # str -> 'YYYY-MM-DD'
        ]
        for param_name in parameters:
            if param_name == 'report_date':
                valid   = [f'{datetime.now().strftime("%Y-%m-%d")}']
                invalid = ['a', 1, 2.3, False]
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
        self.api_name               = 'dailypothole_add_user_api'
        self.post_response_json_key_specifications = [
            {'name': 'user_id'  , 'null': False}
            ,{'name': 'username' , 'null': False}
            ,{'name': 'is_admin' , 'null': False}
        ]

        self.valid_username         = 'some_random_name'

        self.valid_payloads = [
            {
                'username_input'    : self.valid_username,
                'is_admin_input'    : 'False',
            }
            ,{
                'username_input'    : self.valid_username,
                'is_admin_input'    : 'True',
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
            new_user = TblUser.objects.using('DailyPothole').get(username__exact=self.valid_username)
        except:
            ...#Do nothing
        else:
            new_user.delete(using='DailyPothole')

    def test_with_valid_data(self):
        grant_admin_status()

        for payload in self.valid_payloads:
            self.remove_test_user_if_exists()
            response_content = self.post_and_get_json_response( payload )

            ## Check that the request was successful
            self.assertTrue(response_content['post_success'],
                f"api call was not successfully with valid data: {response_content['post_msg']}")

            ## Check that the returned JSON Response got all the data it required
            self.assert_response_satisfy_param_requirements(response_content=response_content)

            ## Check if data was saved correctly
            saved_object = TblUser.objects.using('DailyPothole').get(username__exact=self.valid_username)

            self.assert_post_key_update_equivalence(key_name='username', key_value=payload['username_input'], db_value=saved_object.username)
            self.assert_post_key_update_equivalence(key_name='is_admin', key_value=payload['is_admin_input'], db_value=str(saved_object.is_admin))

    def test_data_validation(self):
        grant_admin_status()

        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name    # Accepted type
            "username_input"    # str -> username
            ,"is_admin_input"   # str -> 'True' or 'False'
        ]
        for param_name in parameters:
            if param_name == 'username_input':
                valid   = [self.valid_username]
                invalid = [1, 2.3, False, None]
            elif param_name == 'is_admin_input':
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
        self.api_name               = 'dailypothole_update_user_api'
        self.post_response_json_key_specifications = [
            {'name': 'user_id'  , 'null': False}
            ,{'name': 'username' , 'null': False}
            ,{'name': 'is_admin' , 'null': False}
        ]

        self.valid_payloads = [
            {
                'table'     : 'tblUser',
                'column'    : 'IsAdmin',
                'id'        : self.user_obj.username,
                'new_value' : 'False'
            }
            ,{
                'table'     : 'tblUser',
                'column'    : 'IsAdmin',
                'id'        : self.user_obj.username,
                'new_value' : 'True'
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
            response_content = self.post_and_get_json_response( payload )

            ## Check that the request was successful
            self.assertTrue(response_content['post_success'],
                f"api call was not successfully with valid data: {response_content['post_msg']}")

            ## Check that the returned JSON Response got all the data it required
            self.assert_response_satisfy_param_requirements(response_content=response_content)

            ## Check if data was saved correctly
            saved_object = TblUser.objects.using('DailyPothole').get(username__exact=self.user_obj.username)

            if payload['column'] == 'IsAdmin':
                self.assert_post_key_update_equivalence(key_name=payload['column'], key_value=payload['new_value'], db_value=str(saved_object.is_admin))
            else:
                raise ValueError(f"{payload['column']} is not recognized as a valid column value in the payload")

    def test_data_validation(self):
        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name    # Accepted type
            'table'             # str -> currently only accepts 'tblUser'
            ,'column'           # str -> currently only accepts 'IsAdmin'
            ,'id'               # str -> user id
            ,'new_value'        # str -> the new value to set to the column name
        ]
        for param_name in parameters:
            if param_name == 'table':
                valid   = ['tblUser']
                invalid = [1, 2.3, False, None, 'sdfds']
            elif param_name == 'column':
                valid   = ['IsAdmin']
                invalid = [1, 2.3, False, None, 'sdfds']
            elif param_name == 'id':
                valid   = [self.user_obj.username]
                invalid = [2.3, False, None, 3]
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
        self.api_name               = 'dailypothole_delete_user_api'
        self.post_response_json_key_specifications = []

        self.valid_username         = 'some_random_name'

        self.valid_payloads = [
            {
                'windows_username': self.valid_username,
            }
        ]

    @classmethod
    def tearDownClass(self):
        tear_down()
        try:
            test_user = TblUser.objects.using('DailyPothole').get(username__exact=self.valid_username)
        except ObjectDoesNotExist as e:
            ... ## Good, do nothing
        except:
            raise
        else:
            test_user.delete(using='DailyPothole')

    def test_api_accept_only_admins(self):
        remove_admin_status()

        payload = self.valid_payloads[0]
        content = self.post_and_get_json_response(payload)

        self.assertTrue((content['post_success']==False) and ("not an admin" in content['post_msg']),
            f"api should have detected that user is not an admin and fail\n{content['post_msg']}")

    def add_test_user_if_not_exists(self):
        test_user = TblUser.objects.using('DailyPothole').get_or_create(username=self.valid_username)[0]
        test_user.save(using='DailyPothole')

    def test_with_valid_data(self):
        grant_admin_status()

        for payload in self.valid_payloads:
            self.add_test_user_if_not_exists()
            response_content = self.post_and_get_json_response( payload )

            ## Check that the request was successful
            self.assertTrue(response_content['post_success'],
                f"api call was not successfully with valid data: {response_content['post_msg']}")

            ## Check that the returned JSON Response got all the data it required
            self.assert_response_satisfy_param_requirements(response_content=response_content)

            ## Check if data was deleted correctly
            try:
                saved_object = TblUser.objects.using('DailyPothole').get(username__exact=self.valid_username)
            except ObjectDoesNotExist as e:
                ... ## Good, do nothing
            except Exception as e:
                raise ValueError(f"TestAPIDeleteUser: test_with_valid_data(): {e}")
            else:
                self.assertTrue(False, f"{saved_object.username} still exists in the database, unable to delete user")

    def test_data_validation(self):
        grant_admin_status()

        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name    # Accepted type
            "windows_username"  # str -> username
        ]
        for param_name in parameters:
            if param_name == 'windows_username':
                valid   = [self.valid_username]
                invalid = [1, 2.3, False, None]
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.add_test_user_if_not_exists()
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.add_test_user_if_not_exists()
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPIAddUserPermission(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        self.api_name               = 'dailypothole_add_user_permission_api'
        self.valid_username         = TEST_WINDOWS_USERNAME
        self.post_response_json_key_specifications = [
            {'name': 'permission_id', 'null': False}
            ,{'name': 'username'    , 'null': False}
            ,{'name': 'operation'   , 'null': False}
            ,{'name': 'boro_long'   , 'null': False}
            ,{'name': 'is_active'   , 'null': False}
        ]

        self.valid_payloads = [
            {
                'username_input'    : self.valid_username,
                'operation_input'   : 'BRIDGE PM',
                'boro_input'        : 'BRONX'
            }
            ,{
                'username_input'    : self.valid_username,
                'operation_input'   : 'STREET MAINTENANCE',
                'boro_input'        : 'BRONX'
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
        grant_admin_status()

        for payload in self.valid_payloads:
            tear_down_permissions(windows_username=self.valid_username)
            response_content = self.post_and_get_json_response( payload )

            ## Check that the request was successful
            self.assertTrue(response_content['post_success'],
                f"api call was not successfully with valid data: {response_content['post_msg']}")

            ## Check that the returned JSON Response got all the data it required
            self.assert_response_satisfy_param_requirements(response_content=response_content)

            ## Check if data was saved correctly
            saved_object = TblPermission.objects.using('DailyPothole').get(
                user_id__username__exact                            = payload['username_input']
                ,operation_boro_id__operation_id__operation__exact  = payload['operation_input']
                ,operation_boro_id__boro_id__boro_long__exact       = payload['boro_input']
            )

            self.assert_post_key_update_equivalence(key_name='username' , key_value=payload['username_input']  , db_value=saved_object.user_id.username)
            self.assert_post_key_update_equivalence(key_name='operation', key_value=payload['operation_input'] , db_value=saved_object.operation_boro_id.operation_id.operation)
            self.assert_post_key_update_equivalence(key_name='boro_long', key_value=payload['boro_input']      , db_value=saved_object.operation_boro_id.boro_id.boro_long)

    def test_data_validation(self):
        grant_admin_status()

        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name    # Accepted type
            'username_input'    # str -> username
            ,'operation_input'  # str -> operation name
            ,'boro_input'       # str -> boro name
        ]
        for param_name in parameters:
            if param_name == 'username_input':
                valid   = [self.valid_username]
                invalid = [1, 2.3, False, None]
            elif param_name == 'operation_input':
                valid   = ['BRIDGE PM', 'STREET MAINTENANCE']
                invalid = ['a', 1, 2.3, '-1', '-1.2', '11.567', '2.2', '4.45', None, False]
            elif param_name == 'boro_input':
                valid   = ['QUEENS', 'BRONX']
                invalid = ['a', 1, 2.3, '-1', '-1.2', '11.567', '2.2', '4.45', None, False]
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                tear_down_permissions(windows_username=self.valid_username)
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                tear_down_permissions(windows_username=self.valid_username)
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPIUpdateUserPermission(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        set_up_permissions(operation_boro_pairs=[(DEFAULT_OPERATION, DEFAULT_BORO)])
        self.api_name               = 'dailypothole_update_user_permission_api'
        self.post_response_json_key_specifications = [
            {'name': 'username'  , 'null': False}
            ,{'name': 'operation' , 'null': False}
            ,{'name': 'boro_long' , 'null': False}
        ]

        self.valid_permission_id    = TblPermission.objects.using('DailyPothole').get(
                                        user_id__username__exact=TEST_WINDOWS_USERNAME
                                        ,operation_boro_id__operation_id__operation__exact=DEFAULT_OPERATION
                                        ,operation_boro_id__boro_id__boro_long__exact=DEFAULT_BORO
                                    ).permission_id

        self.valid_payloads = [
            {
                'table'     : 'tblPermission',
                'column'    : 'IsActive',
                'id'        : f'{self.valid_permission_id}',
                'new_value' : 'True'
            }
            ,{
                'table'     : 'tblPermission',
                'column'    : 'IsActive',
                'id'        : self.valid_permission_id,
                'new_value' : 'False'
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
        grant_admin_status()

        for payload in self.valid_payloads:
            response_content = self.post_and_get_json_response( payload )

            ## Check that the request was successful
            self.assertTrue(response_content['post_success'],
                f"api call was not successfully with valid data: {response_content['post_msg']}")

            ## Check that the returned JSON Response got all the data it required
            self.assert_response_satisfy_param_requirements(response_content=response_content)

            ## Check if data was saved correctly
            saved_object = TblPermission.objects.using('DailyPothole').get(
                permission_id=self.valid_permission_id
            )

            self.assert_post_key_update_equivalence(key_name=payload['column'], key_value=payload['new_value'], db_value=str(saved_object.is_active))

    def test_data_validation(self):
        grant_admin_status()

        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name    # Accepted type
            'table'             # str -> Table name
            ,'column'           # str -> Column name of the table
            ,'id'               # str/int -> string formatted int or int: primary key of a row in the Permission table
            ,'new_value'        # str -> the new value to be saved
        ]
        for param_name in parameters:
            if param_name == 'table':
                valid   = ['tblPermission']
                invalid = [1, 2.3, False, None, 'sdf', '']
            elif param_name == 'column':
                valid   = ['IsActive']
                invalid = ['a', 1, 2.3, '-1', '-1.2', '11.567', '2.2', '4.45', None, False, True, '']
            elif param_name == 'id':
                valid   = [f'{self.valid_permission_id}', self.valid_permission_id]
                invalid = ['a', '-1', '-1.2', '11.567', '2.2', '4.45', 5.46, -1, None, False, True, '']
            elif param_name == 'new_value':
                valid   = ['True', 'False']
                invalid = ['a', '-1', '-1.2', '11.567', '2.2', '4.45', 1000, -1, None, False, True, '']
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPIDeleteUserPermission(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        self.api_name               = 'dailypothole_delete_user_permission_api'
        self.post_response_json_key_specifications = []

        self.valid_payloads = [
            {
                'permission_id': None,
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
        grant_admin_status()

        for payload in self.valid_payloads:
            set_up_permissions(operation_boro_pairs=[(DEFAULT_OPERATION, DEFAULT_BORO)])
            self.valid_permission_id = TblPermission.objects.using('DailyPothole').get(
                                        user_id__username__exact=TEST_WINDOWS_USERNAME
                                        ,operation_boro_id__operation_id__operation__exact=DEFAULT_OPERATION
                                        ,operation_boro_id__boro_id__boro_long__exact=DEFAULT_BORO
                                    ).permission_id
            payload['permission_id'] = self.valid_permission_id
            response_content = self.post_and_get_json_response( payload )

            ## Check that the request was successful
            self.assertTrue(response_content['post_success'],
                f"api call was not successfully with valid data: {response_content['post_msg']}")

            ## Check that the returned JSON Response got all the data it required
            self.assert_response_satisfy_param_requirements(response_content=response_content)

            ## Check if data was deleted correctly
            try:
                saved_object = TblPermission.objects.using('DailyPothole').get(permission_id=self.valid_permission_id)
            except ObjectDoesNotExist as e:
                ... ## Good, do nothing
            except Exception as e:
                raise ValueError(f"TestAPIDeleteUser: test_with_valid_data(): {e}")
            else:
                self.assertTrue(False, f"permission_id {saved_object.permission_id} still exists in the database, unable to delete permission")

    def test_data_validation(self):
        grant_admin_status()
        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name    # Accepted type
            'permission_id'     # int -> primary key of a row in the Permission table
        ]
        for param_name in parameters:
            set_up_permissions(operation_boro_pairs=[(DEFAULT_OPERATION, DEFAULT_BORO)])
            self.valid_permission_id = TblPermission.objects.using('DailyPothole').get(
                                        user_id__username__exact=TEST_WINDOWS_USERNAME
                                        ,operation_boro_id__operation_id__operation__exact=DEFAULT_OPERATION
                                        ,operation_boro_id__boro_id__boro_long__exact=DEFAULT_BORO
                                    ).permission_id
            payload['permission_id'] = self.valid_permission_id

            if param_name == 'permission_id':
                valid   = [self.valid_permission_id]
                invalid = ['a', '-1', '-1.2', '11.567', '2.2', '4.45', 5.46, -1, None, False, True, '']
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPIGetCsvExport(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        self.api_name                   = 'dailypothole_get_csv_export_api'
        self.post_response_json_key_specifications = [
            {'name': 'post_csv_bytes'  , 'null': False}
        ]

        self.valid_start_report_date    = f'{( datetime.now() - timedelta(days=7) ).strftime("%Y-%m-%d")}'
        self.valid_end_report_date      = f'{datetime.now().strftime("%Y-%m-%d")}'

        self.valid_payloads = [
            {
                'start_date'    : self.valid_start_report_date,
                'end_date'      : self.valid_end_report_date,
                'operation_list': [DEFAULT_OPERATION, 'STREET MAINTENANCE', 'JETS/NIGHT EMERGENCY'],
                'type_of_query' : 'date_range_summary',
            }
            ,{
                'start_date'    : self.valid_start_report_date,
                'end_date'      : self.valid_end_report_date,
                'operation_list': [DEFAULT_OPERATION, 'STREET MAINTENANCE', 'JETS/NIGHT EMERGENCY'],
                'type_of_query' : 'ytd_range_last_five_years_summary',
            }
            ,{
                'start_date'    : self.valid_start_report_date,
                'end_date'      : self.valid_end_report_date,
                'operation_list': [DEFAULT_OPERATION, 'STREET MAINTENANCE', 'JETS/NIGHT EMERGENCY'],
                'type_of_query' : 'fytd_n_last_week_wo_art_maint',
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
        grant_admin_status()
        for payload in self.valid_payloads:
            response_content = self.post_and_get_json_response( payload )

            ## Check that the request was successful
            self.assertTrue(response_content['post_success'],
                f"api call was not successfully with valid data: {response_content['post_msg']}")

            ## Check that the returned JSON Response got all the data it required
            self.assert_response_satisfy_param_requirements(response_content=response_content)

    def test_data_validation(self):
        grant_admin_status()
        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name    # Accepted type
            'start_date'        # str -> 'YYYY-MM-DD'
            ,'end_date'         # str -> 'YYYY-MM-DD'
            ,'operation_list'   # list of str -> ['BRIDGE PM', 'STREET MAINTENANCE', ...]. This can be null if 'type_of_query' == 'fytd_n_last_week_wo_art_maint'
            ,'type_of_query'    # str -> one of the values in ('date_range_summary', 'ytd_range_last_five_years_summary', 'fytd_n_last_week_wo_art_maint')
        ]
        for param_name in parameters:
            if param_name == 'start_date':
                valid   = [f'{datetime.now().strftime("%Y-%m-%d")}']
                invalid = ['a', 1, 2.3, False, True, '', None]
            elif param_name == 'end_date':
                valid   = [f'{datetime.now().strftime("%Y-%m-%d")}']
                invalid = ['a', 1, 2.3, False, True, '', None]
            elif param_name == 'operation_list':
                valid   = [['BRIDGE PM', 'STREET MAINTENANCE'], ['JETS/NIGHT EMERGENCY']]
                invalid = ['a', 1, 2.3, False, True, '', None, ['a'], [1], [2.3], [False], [True], [''], [None]]
            elif param_name == 'type_of_query':
                valid   = ['date_range_summary', 'ytd_range_last_five_years_summary', 'fytd_n_last_week_wo_art_maint']
                invalid = ['a', 1, 2.3, False, True, '', None]
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)

