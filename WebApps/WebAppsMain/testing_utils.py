import json
from django.urls import reverse
from WebAppsMain.settings import GET_RESPONSE_REQUIRED_CONTEXT_KEYS, POST_RESPONSE_REQUIRED_JSON_KEYS, TEST_WINDOWS_USERNAME


def validate_core_get_api_response_context(response):
    """
        In this django project, a standard GET response to any of the views should have these context variables
        "req_success"
        "err_msg"
        "client_is_admin"
        additinal variables are optional
    """
    for key in GET_RESPONSE_REQUIRED_CONTEXT_KEYS:
        if key not in response.context_data:
            raise ValueError(f"validate_core_get_api_response_context(): Invalid GET response. Requires {GET_RESPONSE_REQUIRED_CONTEXT_KEYS} but there is missing keys from: {response.context_data.keys()}")

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

    for key in POST_RESPONSE_REQUIRED_JSON_KEYS:
        if key not in response_content:
            raise ValueError(f"validate_core_post_api_response_content(): Invalid POST JSON response. Requires {POST_RESPONSE_REQUIRED_JSON_KEYS} but there is missing keys from: {response_content.keys()}")

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

