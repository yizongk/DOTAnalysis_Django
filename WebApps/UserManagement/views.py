from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import generic
from django.http import HttpResponse, JsonResponse
from .models import *
import json
from django.core.serializers.json import DjangoJSONEncoder

# Create your views here.


APP_NAME = "UserManagement"


def user_is_active_admin(username=None):
    try:
        user = WebAppUserMemberships.objects.using('default').get(
            windows_username__windows_username__exact=username
            ,web_app_id__web_app_name__exact=APP_NAME
        )
        if user.is_active:
            return user.is_admin
        else:
            return False
    except Exception as e:
        raise ValueError(f"user_is_active_admin(): {e}")


class HomePageView(TemplateView):
    template_name   = 'UserManagement.template.home.html'
    get_success     = True
    get_error       = None
    client_is_admin = None

    def get_context_data(self, **kwargs):
        ## Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        self.client_is_admin = user_is_active_admin(self.request.user)
        context["client_is_admin"]  = self.client_is_admin
        context["get_success"]      = self.get_success
        context["get_error"]        = self.get_error
        return context


class AboutPageView(TemplateView):
    template_name   = 'UserManagement.template.about.html'
    get_success     = True
    get_error       = None
    client_is_admin = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["get_success"]      = self.get_success
        context["get_error"]        = self.get_error
        context["client_is_admin"]  = self.client_is_admin
        return context


class ContactPageView(TemplateView):
    template_name   = 'UserManagement.template.contact.html'
    get_success     = True
    get_error       = None
    client_is_admin = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["get_success"]      = self.get_success
        context["get_error"]        = self.get_error
        context["client_is_admin"]  = self.client_is_admin
        return context


class ManageWebAppsPageView(generic.ListView):
    template_name           = 'UserManagement.template.managewebapps.html'

    get_success             = False
    get_error               = None
    client_is_admin         = False

    ag_grid_col_def_json    = None
    rows_data_json          = None

    def get_queryset(self):
        ## Check for Active Admins
        self.client_is_admin = user_is_active_admin(self.request.user)

        ## Get the core data
        try:
            ag_grid_col_def = [ ## Need to format this way for AG Grid
                {'headerName': 'Web App ID'     , 'field': 'web_app_id'     , 'suppressMovable': True , 'lockPinned': True , 'cellClass': 'left-pinned' , 'pinned': 'left' , 'width': 80}
                ,{'headerName': 'Web App Name'  , 'field': 'web_app_name'   , 'suppressMovable': True , 'lockPinned': True}
                ,{'headerName': 'Is Active'     , 'field': 'is_active'      , 'suppressMovable': True , 'lockPinned': True}
            ]

            fields_list = [each['field'] for each in ag_grid_col_def]

            web_apps = WebApps.objects.using('default').all().order_by('web_app_id').values(*fields_list)

            self.ag_grid_col_def_json   = json.dumps(list(ag_grid_col_def)  , cls=DjangoJSONEncoder)
            self.rows_data_json         = json.dumps(list(web_apps)         , cls=DjangoJSONEncoder)

        except Exception as e:
            self.get_success    = False
            self.get_error      = f"ManageWebAppsPageView(): get_queryset(): {e}"
            return None

        self.get_success = True
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["get_success"]          = self.get_success
        context["get_error"]            = self.get_error
        context["client_is_admin"]      = self.client_is_admin

        context["ag_grid_col_def_json"] = self.ag_grid_col_def_json
        context["rows_data_json"]       = self.rows_data_json
        return context
