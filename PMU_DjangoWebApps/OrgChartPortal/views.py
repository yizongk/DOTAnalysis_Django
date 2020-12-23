from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import generic
from .models import *


# Create your views here.
class HomePageView(TemplateView):
    template_name = 'OrgChartPortal.template.home.html'
    client_is_admin = False

    def get_context_data(self, **kwargs):
        try:
            ## Call the base implementation first to get a context
            context = super().get_context_data(**kwargs)
            context["client_is_admin"] = self.client_is_admin
            return context
        except Exception as e:
            context["client_is_admin"] = False
            return context

class AboutPageView(TemplateView):
    template_name = 'OrgChartPortal.template.about.html'

class ContactPageView(TemplateView):
    template_name = 'OrgChartPortal.template.contact.html'

def get_allowed_list_of_wu(username):
    try:
        wu_query = TblPermissions.objects.using('OrgChartWrite').filter(
            windows_username=username,
        ).order_by('wu')

        if wu_query.count() > 0:
            return {
                "success": True,
                "err": "",
                "wu_list": [each.wu for each in wu_query],
            }
        return {
            "success": False,
            "err": "Cannot find any WU permissions for '{}'".format(username),
        }
    except Exception as e:
        print("Exception: OrgChartPortal: get_allowed_list_of_wu(): {}".format(e))
        return {
            "success": False,
            "err": 'Exception: OrgChartPortal: get_allowed_list_of_wu(): {}'.format(e),
        }

class EmpGridPageView(generic.ListView):
    template_name = 'OrgChartPortal.template.empgrid.html'
    context_object_name = 'emp_entries'

    req_success = False
    err_msg = ""

    client_is_admin = False

    def get_queryset(self):
        ## Check for Active Admins
        # is_active_admin = user_is_active_admin(self.request.user)
        # if is_active_admin["success"] == True:
        #     self.client_is_admin = True
        # else:
        #     self.req_success = False

        ## Get the core data
        try:
            if self.client_is_admin:
                pms_entries = TblEmployees.objects.using('OrgChartWrite').all().order_by('wu')
            else:
                allowed_wu_list_obj = get_allowed_list_of_wu(self.request.user)
                if allowed_wu_list_obj['success'] == False:
                    raise ValueError('get_allowed_list_of_wu() failed: {}'.format(allowed_wu_list_obj['err']))
                else:
                    allowed_wu_list = allowed_wu_list_obj['wu_list']

                pms_entries = TblEmployees.objects.using('OrgChartWrite').filter(
                    wu__in=allowed_wu_list,
                ).order_by('wu')
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: EmpGridPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return TblEmployees.objects.none()

        self.req_success = True
        return pms_entries

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)

            context["req_success"] = self.req_success
            context["err_msg"] = self.err_msg

            context["client_is_admin"] = self.client_is_admin
            return context
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: get_context_data(): {}".format(e)
            print(self.err_msg)

            context = super().get_context_data(**kwargs)
            context["req_success"] = self.req_success
            context["err_msg"] = self.err_msg

            context["client_is_admin"] = False
            return context

