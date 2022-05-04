from django.http import JsonResponse
import json

def post_request_decorator(func):
    """
        Wraps an POST api function with some helper functions

        func(request, json_blob, remote_user) needs to have two kwargs
            @request:       The request object will be passed in
            @json_blob:     The request.body converted to json will be passed in
            @remote_user:   The request.user.username will be passed in
    """

    def wrap(request):
        ## Only access POST request
        if request.method != "POST":
            return JsonResponse({
                "post_success"  : False,
                "post_msg"      : f"{request.method} HTTP request not supported",
                "post_data"     : None,
            })

        ## Authenticate User
        remote_user = None
        if request.user.is_authenticated:
            remote_user = request.user.username
        else:
            print('Warning: AddUser(): UNAUTHENTICATE USER!')
            return JsonResponse({
                "post_success"  : False,
                "post_msg"      : "AddUser():\n\nUNAUTHENTICATE USER!",
                "post_data"     : None,
            })

        ## Read the json request body
        try:
            json_blob = json.loads(request.body)
        except Exception as e:
            return JsonResponse({
                "post_success"  : False,
                "post_msg"      : f"Unable to load request.body as a json object: {e}",
                "post_data"     : None,
            })

        return func(request=request, json_blob=json_blob, remote_user=remote_user)

    return wrap