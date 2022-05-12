from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import generic
from django.http import HttpResponse, JsonResponse
from .models import *

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
