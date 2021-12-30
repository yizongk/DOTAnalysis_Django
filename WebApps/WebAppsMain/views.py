from django.shortcuts import redirect

def redirect_to_pdam_gate(request):
    response = redirect('http://dotanalytics01')
    return response