from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import generic
from django.http import HttpResponse, JsonResponse
from .models import *
import json
from django.core.serializers.json import DjangoJSONEncoder
from WebAppsMain.settings import WEB_APP_NAME_USER_MANAGEMENT

# Create your views here.


def user_is_enabled(username=None):
    """check active directory to see if user is enabled"""
    try:
        ad_user = ActiveDirectory.objects.using('default').get(
            windows_username__exact=username
        )

        return ad_user.enabled
    except Exception as e:
        raise ValueError(f"user_is_enabled(): {e}")


def user_is_active_admin(username=None):
    """check user app membership to see if membership is active and is admin"""
    try:
        if not user_is_enabled(username=username):
            return False

        user_app_membership = WebAppUserMemberships.objects.using('default').get(
            windows_username__windows_username__exact=username
            ,web_app_id__web_app_name__exact=WEB_APP_NAME_USER_MANAGEMENT
        )

        if user_app_membership.is_active:
            return user_app_membership.is_admin
        else:
            return False
    except Exception as e:
        raise ValueError(f"user_is_active_admin(): {e}")


def user_is_active(username=None):
    """check user app membership to see if membership is active"""
    try:
        if not user_is_enabled(username=username):
            return False

        user_app_membership = WebAppUserMemberships.objects.using('default').get(
            windows_username__windows_username__exact=username
            ,web_app_id__web_app_name__exact=WEB_APP_NAME_USER_MANAGEMENT
        )

        return user_app_membership.is_active
    except Exception as e:
        raise ValueError(f"user_is_active(): {e}")


class HomePageView(TemplateView):
    template_name   = 'UserManagement.template.home.html'
    get_success     = True
    get_error       = None
    client_is_admin = None

    def get_context_data(self, **kwargs):
        if not user_is_active(username=self.request.user):
            self.get_success = False
            self.get_error = f"'{self.request.user}' is not an active user of the application"

        ## Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        self.client_is_admin = user_is_active_admin(username=self.request.user)
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
        if not user_is_active(username=self.request.user):
            self.get_success = False
            self.get_error = f"'{self.request.user}' is not an active user of the application"

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
        if not user_is_active(username=self.request.user):
            self.get_success = False
            self.get_error = f"'{self.request.user}' is not an active user of the application"

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
        try:
            ## Check for active user
            if not user_is_active(username=self.request.user):
                raise ValueError(f"'{self.request.user}' is not an active user of the application")

            ## Check for Active Admins
            self.client_is_admin = user_is_active_admin(username=self.request.user)
            if not self.client_is_admin:
                raise ValueError(f"'{self.request.user}' is not an admin")

            ## Get the core data
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
