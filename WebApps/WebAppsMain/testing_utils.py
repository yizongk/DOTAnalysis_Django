import json
from django.urls import reverse
from WebAppsMain.settings import POST_RESPONSE_REQUIRED_KEYS


def get_to_api(client, api_name, remote_user):
    """return the response of the GET api call"""
    return client.get(
        reverse(api_name)
        ,REMOTE_USER=remote_user
    )


def decode_json_response_for_content(response):
    """reponse.content is in binary, need to decode it to get access to it in python dictinary format"""
    return json.loads(response.content.decode('utf-8'))


def validate_core_post_api_response_content(response_content):
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

    for key in POST_RESPONSE_REQUIRED_KEYS:
        if key not in response_content:
            return False

    return True


def post_to_api(client, api_name, payload, remote_user):
    """return the response of the POST api call"""
    response = client.post(
        reverse(api_name)
        ,data           = json.dumps(payload)
        ,content_type   = 'application/json'
        ,REMOTE_USER    = remote_user
    )

    response_content = decode_json_response_for_content(response=response)
    if not validate_core_post_api_response_content(response_content=response_content):
        raise ValueError(f"post_to_api(): {reverse(api_name)} returned invalid POST JSON response. Requires {POST_RESPONSE_REQUIRED_KEYS} but there is missing keys from: {response_content.keys()}")

    return response

