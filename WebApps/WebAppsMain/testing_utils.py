import json
from django.urls import reverse
from WebAppsMain.settings import APP_DEFINED_HTTP_GET_CONTEXT_KEYS, APP_DEFINED_HTTP_POST_JSON_KEYS, TEST_WINDOWS_USERNAME, DJANGO_DEFINED_GENERIC_LIST_VIEW_CONTEXT_KEYS, DJANGO_DEFINED_GENERIC_DETAIL_VIEW_CONTEXT_KEYS
import copy
import unittest
from django.test import Client


class HttpGetTestCase(unittest.TestCase):
    client                          = Client()
    regular_views                   = []        ## Required by sub class. Set it in def setUpClass()
    admin_views                     = []        ## Required by sub class. Set it in def setUpClass()

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
                            self.additional_context_requirements =   [
                                                                {
                                                                    'view': 'some_view_name'
                                                                    ,'additional_context_keys': ['key_name_1', 'key_name_2', ...]
                                                                    ,'qa_fct': self.__more_qa_asserts      ## Assumes this fct has a reference to self.assertTrue() etc
                                                                }
                                                            ]

                        def __more_qa_asserts(self, response):
                            self.assertTrue(response[...]=True, '...')
                            ...

                        self.test_views_response_data()             ## Implicitly will decode @self.additional_context_requirements and use it.
        """
        django_default_context_keys = DJANGO_DEFINED_GENERIC_LIST_VIEW_CONTEXT_KEYS + DJANGO_DEFINED_GENERIC_DETAIL_VIEW_CONTEXT_KEYS
        response_context_keys = response.context_data.keys()

        for response_context_key in response_context_keys:
            self.assertTrue( (response_context_key in (view_defined_additional_context_keys + APP_DEFINED_HTTP_GET_CONTEXT_KEYS + django_default_context_keys) ),
                f"{view} response got back a context key that shouldn't exist. Please add this new key to the test suite or change the view: '{response_context_key}'")

        for additional_context_key in view_defined_additional_context_keys:
            self.assertTrue(additional_context_key in response_context_keys,
                f"{view} response is missing this view defined required context key '{additional_context_key}'")

        if view_defined_additional_context_keys is not None and additional_context_keys_data_qa_fct is not None:
            additional_context_keys_data_qa_fct(self, response)

    def assert_response_status_200(self):
        for view in self.regular_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertEqual(response.status_code, 200, f"'{view}' did not return status code 200")

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertEqual(response.status_code, 200, f"'{view}' did not return status code 200")

    def assert_user_access_on_normal_and_admin_view(self):
        """Pass if normal user get access to normal view, and denied access to admin views"""
        for view in self.regular_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertTrue(response.context['get_success'], f"'{view}' did not return get_success True on a regular view for a non-admin user\n    {response.context['get_error']}")

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertFalse(response.context['get_success'], f"'{view}' returned get_success True on an admin view for a non-admin user\n    {response.context['get_error']}")
            self.assertTrue("not an admin" in response.context['get_error'], f"'{view}' does not have correct error message on an admin view when user is non-admin (must contain 'not an admin' in the error message)\n    {response.context['get_error']}")

    def assert_admin_access_on_normal_and_admin_view(self):
        """Pass if admin user get access to normal view, and access to admin views"""
        for view in self.regular_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertTrue(response.context['get_success'], f"'{view}' did not return get_success True on a regular view for an admin user\n    {response.context['get_error']}")

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertTrue(response.context['get_success'], f"'{view}' did not return get_success True on an admin view for an admin user\n    {response.context['get_error']}")

    def assert_inactive_user_no_access_on_normal_and_admin_view(self):
        """Pass if inactive user (admin or not) get denied access to normal view and admin views"""
        for view in self.regular_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertFalse(response.context['get_success'], f"'{view}' returned get_success True on a regular view for an inactive user\n    {response.context['get_error']}")
            self.assertTrue("not an active user" in response.context['get_error'], f"'{view}' does not have correct error message on a regular view when user is inactive (must contain 'not an active user' in the error message)\n    {response.context['get_error']}")

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)
            self.assertFalse(response.context['get_success'], f"'{view}' returned get_success True on an admin view for an non-admin user\n    {response.context['get_error']}")
            self.assertTrue("not an active user" in response.context['get_error'], f"'{view}' does not have correct error message on an admin view when user is inactive (must contain 'not an active user' in the error message)\n    {response.context['get_error']}")

    def assert_additional_context_data(self, additional_requirements=None):
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
            if additional_requirements is not None and view in [each['view'] for each in additional_requirements]:
                len_of_fouund_requirements = len([x for x in additional_requirements if view == x['view']])
                if (len_of_fouund_requirements != 1):
                    raise ValueError(f"HttpGetTestCase: assert_additional_context_data(): argument @additional_requirements got back more than 1 requirement with view name: '{view}' (found {len_of_fouund_requirements}). Should only have one requirement per view name")

                view_additional_req     = next(x for x in additional_requirements if view == x['view'])
                additional_context_keys = view_additional_req['additional_context_keys']
                qa_test                 = view_additional_req['qa_fct']

                self.__verify_response_with_required_additional_context_data(view=view, response=response, view_defined_additional_context_keys=additional_context_keys, additional_context_keys_data_qa_fct=qa_test)
            else:
                ## verify additional context data as [], so that it can detect unrecognized context variable
                self.__verify_response_with_required_additional_context_data(view=view, response=response, view_defined_additional_context_keys=[])

        for view in self.admin_views:
            response = get_to_api(client=self.client, api_name=view, remote_user=TEST_WINDOWS_USERNAME)

            ## When caller is a normal non-admin user, don't check the additional_requirements
            if response.context['get_error'] is not None and "not an admin" in response.context['get_error']:
                continue

            if additional_requirements is not None and view in [each['view'] for each in additional_requirements]:
                len_of_fouund_requirements = len([x for x in additional_requirements if view == x['view']])
                if (len_of_fouund_requirements != 1):
                    raise ValueError(f"HttpGetTestCase: assert_additional_context_data(): argument @additional_requirements got back more than 1 requirement with view name: '{view}' (found {len_of_fouund_requirements}). Should only have one requirement per view name")

                view_additional_req     = next(x for x in additional_requirements if view == x['view'])
                additional_context_keys = view_additional_req['additional_context_keys']
                qa_test                 = view_additional_req['qa_fct']

                self.__verify_response_with_required_additional_context_data(view=view, response=response, view_defined_additional_context_keys=additional_context_keys, additional_context_keys_data_qa_fct=qa_test)
            else:
                ## verify additional context data as [], so that it can detect unrecognized context variable
                self.__verify_response_with_required_additional_context_data(view=view, response=response, view_defined_additional_context_keys=[])


class HttpPostTestCase(unittest.TestCase):
    """
        This class contains some standard functions that help test any HTTP POST requests in this Django project

        Each test case class must define the self.api_name in the setUpClass(self).
        Sample usage:

        class TestSomeThing(HttpPostTestCase):
            @classmethod
            def setUpClass(self):
                self.api_name                               = 'name_of_your_view'   ## This is REQUIRED
                self.post_response_json_key_specifications  = []                    ## This is REQUIRED, set it to empty list if is has none. Expects the format to be like this:
                                                                                [
                                                                                    {name: '...', null: False}   ## if null = True, the param is allowed to be None
                                                                                    ,{name: '...', null: True}
                                                                                    ,{name: '...', null: ...}
                                                                                    ,...
                                                                                ]

            @classmethod
            def tearDownClass(self):
                pass                                    ## Optional

    """
    client                                  = Client()
    api_name                                = None      ## Required by sub class. Set it in def setUpClass()
    post_response_json_key_specifications   = None      ## Required by sub class. Set it in def setUpClass()

    def __post_to_api(self, payload):
        """Returns the response after calling the update api, as a dict. Will not pass if status_code is not 200"""
        response = post_to_api(
            client      = self.client,
            api_name    = self.api_name,
            payload     = payload,
            remote_user = TEST_WINDOWS_USERNAME)

        self.assertEqual(response.status_code, 200, f"'{self.api_name}' did not return status code 200")

        return response

    def post_and_get_json_response(self, payload):
        return decode_json_response_for_content( self.__post_to_api(payload) )

    def assert_request_param_good(self, valid_payload, testing_param_name, testing_data, param_is_good_fct=None):
        """
            Assumes @valid_payload to contain a full payload that has all valid data and should allow the api to return successfully

            if @param_is_good_fct is not None, it will assert @param_is_good_fct is True instead of assert post_success == True
                @param_is_good_fct is a function that will take in the response content as its only argument, and should return True if response content is good or False otherwise.
        """
        payload                     = copy.deepcopy(valid_payload) ## if not deepcopy, it will default to do a shallow copy
        payload[testing_param_name] = testing_data
        response                    = self.__post_to_api(payload=payload)
        content                     = decode_json_response_for_content(response)

        assert_failed_msg = f"POST request failed. Parameter '{testing_param_name}' should accept: '{testing_data}' ({type(testing_data)})\n{content}"

        if param_is_good_fct is not None:
            self.assertTrue(
                param_is_good_fct(content),
                assert_failed_msg)
        else:
            self.assertEqual(
                content['post_success'], True,
                assert_failed_msg)

    def assert_request_param_bad(self, valid_payload, testing_param_name, testing_data, param_is_good_fct=None):
        """
            Assumes @valid_payload to contain a full payload that has all valid data and should allow the api to return successfully

            if @param_is_good_fct is not None, it will assert post_msg == @param_is_good_fct instead of assert post_success == True
        """
        payload                     = copy.deepcopy(valid_payload) ## if not deepcopy, it will default to do a shallow copy
        payload[testing_param_name] = testing_data
        response                    = self.__post_to_api(payload=payload)
        content                     = decode_json_response_for_content(response)

        assert_failed_msg = f"POST request succeded. Parameter '{testing_param_name}' should NOT accept: '{testing_data}' ({type(testing_data)})\n{content}"

        if param_is_good_fct is not None:
            self.assertTrue(
                param_is_good_fct(content),
                assert_failed_msg)
        else:
            self.assertEqual(
                content['post_success'], False,
                assert_failed_msg)

    def assert_response_has_param(self, response_content, response_param_name):
        self.assertTrue(response_param_name in response_content['post_data'],
            f"'{response_param_name}' is not in the response: {response_content['post_data']}")

    def assert_response_has_param_and_not_null(self, response_content, response_param_name):
        self.assert_response_has_param(response_content=response_content, response_param_name=response_param_name)
        self.assertTrue(response_content['post_data'][response_param_name] is not None,
            f"response['post_data']['{response_param_name}'] can't be null: {response_content['post_data']}")

    def assert_response_satisfy_param_requirements(self, response_content):
        """
        Checks that the response param names in "post_data" match the criteria set by @self.post_response_json_key_specifications
        If response got extra param names in "post_data" that isn't in the @self.post_response_json_key_specifications, this will raise an error.

        Expects @self.post_response_json_key_specifications to be of this format:
            [
                {name: '...', null: False}   ## if null = True, the param is allowed to be None
                ,{name: '...', null: True}
                ,{name: '...', null: ...}
                ,...
            ]
        """
        if type(self.post_response_json_key_specifications) is not list:
            raise ValueError(f"assert_response_satisfy_param_requirements(): self.post_response_json_key_specifications is not a list: {type(self.post_response_json_key_specifications)}")
        elif len(self.post_response_json_key_specifications) == 0 and response_content['post_data'] is None:
            ## Nothing to check, specification didn't specify any, and response got nothing in "post_data".
            return
        elif len(self.post_response_json_key_specifications) != 0 and response_content['post_data'] is None:
            ## specification is set, but there's no "post_data" in the response
            raise ValueError(f"response_content['post_data'] returned None even though it is expected to have JSON keys specified by the @self.post_response_json_key_specifications")

        required_propeties = ['name', 'null']
        for param_specification in self.post_response_json_key_specifications:
            ## Make sure the self.post_response_json_key_specifications follows the correct format
            for each_required_property in required_propeties:
                if each_required_property not in param_specification:
                    raise ValueError(f"assert_response_satisfy_param_requirements(): param_specification is missing this property: '{each_required_property}'")

            if type(param_specification['name']) is not str:
                raise ValueError(f"assert_response_satisfy_param_requirements(): param_specification['name'] must be a str.")
            if type(param_specification['null']) is not bool:
                raise ValueError(f"assert_response_satisfy_param_requirements(): param_specification['null'] must be a bool.")

            ## Check the response param to the given param specification
            if param_specification['null']:
                self.assert_response_has_param(response_content=response_content, response_param_name=param_specification['name'])
            else:
                self.assert_response_has_param_and_not_null(response_content=response_content, response_param_name=param_specification['name'])

        ## Make sure that the response don't got any extra param names that was specified by the caller
        specified_required_names = [each['name'] for each in self.post_response_json_key_specifications]
        for actual_response_param_name in response_content['post_data']:
            if actual_response_param_name not in specified_required_names:
                raise ValueError(f"assert_response_satisfy_param_requirements(): response got a param name '{actual_response_param_name}' that is not specified in the @self.post_response_json_key_specifications. Please add it to the test suite")

    def assert_post_key_update_equivalence(self, key_name, key_value, db_value):
        self.assertEqual(str(key_value), str(db_value),
            f"POST post_data key '{key_name}' didn't save correctly: '{key_value}' input-->database '{db_value}'" )

    def assert_post_key_lookup_equivalence(self, key_name, key_value, db_value):
        self.assertEqual(str(key_value), str(db_value),
            f"POST post_data key '{key_name}' didn't look up correctly: '{db_value}' database-->response '{key_value}'" )

    def assert_post_with_valid_payload_is_success(self, payload):
        """
            POST the payload, assert post_success is True, and assert that the response got back all the required post_data keys and only those keys and nothing else
            return the response content
        """
        response_content = self.post_and_get_json_response(payload)

        ## Check that the request was successful
        self.assertTrue(response_content['post_success'],
            f"api call was not successfully with valid data: {response_content['post_msg']}")

        ## Check that the returned JSON Response got all the data it required
        self.assert_response_satisfy_param_requirements(response_content=response_content)

        return response_content


def validate_core_get_api_response_context(response):
    """
        In this django project, a standard GET response to any of the views should have these context variables
        "get_success"
        "get_error"
        "client_is_admin"
        additinal variables are optional
    """
    for key in APP_DEFINED_HTTP_GET_CONTEXT_KEYS:
        if key not in response.context_data:
            raise ValueError(f"validate_core_get_api_response_context(): Invalid GET response. Requires {APP_DEFINED_HTTP_GET_CONTEXT_KEYS} but there is missing keys from: {response.context_data.keys()}")

    return True


def validate_core_post_api_response_content(response):
    """
        Validates our project's standard JSON response.
        The standard response is a variation of the JSend standard: https://github.com/omniti-labs/jsend
        Looks like this:
        {
            "post_success": ...
            ,"post_msg": ...
            ,"post_data": ...
        }

        It is allowed to have additional keys to the required ones. For example:
        {
            "post_success": ...
            ,"post_msg": ...
            ,"post_data": ...
            ,"var_1": ...
            ,"var_2": ...
            ...
        }
    """
    response_content = decode_json_response_for_content(response=response)

    for key in APP_DEFINED_HTTP_POST_JSON_KEYS:
        if key not in response_content:
            raise ValueError(f"validate_core_post_api_response_content(): Invalid POST JSON response. Requires {APP_DEFINED_HTTP_POST_JSON_KEYS} but there is missing keys from: {response_content.keys()}")

    return True


def get_to_api(client, api_name, remote_user=TEST_WINDOWS_USERNAME):
    """return the response of the GET api call. Defaults to user @TEST_WINDOWS_USERNAME"""
    try:
        response = client.get(
            reverse(api_name)
            ,REMOTE_USER=remote_user
        )

        validate_core_get_api_response_context(response=response)

        return response
    except Exception as e:
        raise ValueError(f"get_to_api(): GET to {reverse(api_name)}: {e}")


def decode_json_response_for_content(response):
    """reponse.content is in binary, need to decode it to get access to it in python dictinary format"""
    return json.loads(response.content.decode('utf-8'))


def post_to_api(client, api_name, payload, remote_user=TEST_WINDOWS_USERNAME):
    """return the response of the POST api call. Defaults to user @TEST_WINDOWS_USERNAME"""
    try:
        response = client.post(
            reverse(api_name)
            ,data           = json.dumps(payload)
            ,content_type   = 'application/json'
            ,REMOTE_USER    = remote_user
        )

        validate_core_post_api_response_content(response=response)

        return response
    except Exception as e:
        raise ValueError(f"post_to_api(): POST to {reverse(api_name)}: {e}")

