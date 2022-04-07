from django.test import Client
import unittest
from .models import *
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.urls import reverse
import json
from django.contrib import auth
from django.utils import timezone
import copy

### DO NOT RUN THIS IN PROD ENVIRONMENT

# Create your tests here.

test_windows_username = 'test_user'

def decode_response_byte_for_content(response):
    return json.loads(response.content.decode('utf-8'))


def post_to_api(client, api_name, payload, remote_user):
    """return the response of the POST api call. Will raise exception if status_code is not 200"""
    response = client.post(
        reverse(api_name)
        ,data           = json.dumps(payload)
        ,content_type   = 'application/json'
        ,REMOTE_USER    = remote_user
    )

    if (response.status_code != 200):
        raise ValueError(f"post_to_api(): '{api_name}' did not return status code 200")

    return response


class TestAPIUpdatePotholesData(unittest.TestCase):
    """methods that starts with name 'test...' are the methods be called by unittest"""
    def setUp(self):
        # user=User.objects.get_or_create(username='testuser')[0]
        self.test_windows_username          = test_windows_username
        self.client                         = Client()

        self.valid_operation                = 'BRIDGE PM'
        self.valid_borough                  = 'QUEENS'
        self.valid_date                     = f'{datetime.now().strftime("%Y-%m-%d")}'
        self.valid_crew_count               = 1
        self.valid_holes_repaired           = 2
        self.valid_planned_crew_count       = 3

        self.user_obj = TblUser.objects.using('DailyPothole').get_or_create(
            username=test_windows_username
            ,is_admin=False
        )[0]

        self.update_api_name                = 'dailypothole_update_potholes_data_api'

        operation_boro = TblOperationBoro.objects.using('DailyPothole').get(
            operation_id__operation__exact=self.valid_operation
            ,boro_id__boro_long__exact=self.valid_borough
            ,is_active=True
        )

        TblPermission.objects.using('DailyPothole').get_or_create(
            user_id=self.user_obj
            ,operation_boro_id=operation_boro
            ,is_active=True
        )[0]

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


    def __post_to_update_api(self, payload):
        """Returns the response after calling the update api, as a dict"""
        return post_to_api(
            client      = self.client,
            api_name    = self.update_api_name,
            payload     = payload,
            remote_user = self.test_windows_username)


    def test_update_with_valid_data(self):
        for payload_type in self.valid_payload:
            payload = self.valid_payload[payload_type]
            response_content = decode_response_byte_for_content( self.__post_to_update_api(payload) )

            ## Check that the request was successful
            self.assertEqual(response_content['post_success'], True,
                f"payload_type '{payload_type}': update was not successfully with valid data")

            ## Check if data was saved correctly
            saved_object = TblPotholeMaster.objects.using('DailyPothole').get(
                repair_date=self.valid_date
                ,operation_boro_id__operation_id__operation__exact=self.valid_operation
                ,operation_boro_id__boro_id__boro_long__exact=self.valid_borough
            )

            if payload_type == 'PotholeData':
                self.assertEqual(
                    self.valid_crew_count,
                    saved_object.repair_crew_count,
                    f"payload_type '{payload_type}': [repair_crew_count] didn't save correctly: '{self.valid_crew_count}' input-->database '{saved_object.repair_crew_count}'" )
                self.assertEqual(
                    self.valid_holes_repaired,
                    saved_object.holes_repaired,
                    f"payload_type '{payload_type}': [holes_repaired] didn't save correctly: '{self.valid_holes_repaired}' input-->database '{saved_object.holes_repaired}'" )
            elif payload_type == 'TodayCrewData':
                self.assertEqual(
                    self.valid_planned_crew_count,
                    saved_object.daily_crew_count,
                    f"payload_type '{payload_type}': [daily_crew_count] didn't save correctly: '{self.valid_planned_crew_count}' input-->database '{saved_object.daily_crew_count}'" )
            else:
                raise ValueError( f"UpdatePotholesData: payload_type not recognized in test case: '{payload_type}'" )

            self.assertTrue(  (timezone.now() - saved_object.last_modified_timestamp).total_seconds() < 10 , f"payload_type '{payload_type}': [last_modified_timestamp] didn't save correctly: '{saved_object.last_modified_timestamp.strftime('%Y-%m-%d %H:%M:%S')}' input-->database '{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}'. Cannot exceed more than 10 seconds difference" )
            self.assertEqual( saved_object.last_modified_by_user_id.user_id  , self.user_obj.user_id , f"payload_type '{payload_type}': [last_modified_by_user_id] didn't save correctly: '{saved_object.last_modified_by_user_id.user_id}' input-->database '{self.user_obj.user_id}'" )


    def __assert_request_param_good(self, valid_payload, testing_param_name, testing_data):
        payload                     = copy.deepcopy(valid_payload) ## if not deepcopy, it will default to do a shallow copy
        payload[testing_param_name] = testing_data
        response                    = self.__post_to_update_api(payload=payload)
        content                     = decode_response_byte_for_content(response)

        self.assertEqual(
            content['post_success'], True,
            f"POST request failed. Parameter '{testing_param_name}' should accept: '{testing_data}'")


    def __assert_request_param_bad(self, valid_payload, testing_param_name, testing_data):
        payload                     = copy.deepcopy(valid_payload) ## if not deepcopy, it will default to do a shallow copy
        payload[testing_param_name] = testing_data
        response                    = self.__post_to_update_api(payload=payload)
        content                     = decode_response_byte_for_content(response)

        self.assertEqual(
            content['post_success'], False,
            f"POST request succeded. Parameter '{testing_param_name}' should NOT accept: '{testing_data}'")


    def test_update_data_validation(self):
        f"""Testing {self.update_api_name} data validation"""

        ## For PotholeData
        payload = self.valid_payload['PotholeData']
        parameters = [
            # Parameter name    # Accepted type
            "request_type"      # str   -> ['PotholeData']
            ,"operation"        # str   -> [operation_names*]
            ,"borough"          # str   -> [boro_names*]
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
                raise ValueError(f"UpdatePotholesData: test_update_data_validation(): PotholeData -> paremter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.__assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.__assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


        ## For TodayCrewData
        payload = self.valid_payload['TodayCrewData']
        parameters = [
            "request_type"          # str   -> ['TodayCrewData']
            ,"operation"            # str   -> [operation_names*]
            ,"borough"              # str   -> [boro_names*]
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
                raise ValueError(f"UpdatePotholesData: test_update_data_validation(): TodayCrewData -> paremter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.__assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.__assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)



