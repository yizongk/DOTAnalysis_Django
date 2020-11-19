from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import generic
from .models import *

## Check if remote user is admin and is active
def user_is_active_admin(username):
    try:
        admin_query = Admins.objects.filter(
            window_username=username,
            active=True, ## Filters for active Admins
        )
        if admin_query.count() > 0:
            return {
                "success": True,
                "err": "",
            }
        return {
            "success": False,
            "err": '{} is not an active Admin'.format(username),
        }
    except Exception as e:
        print("Exception: FleetDataCollection: user_is_active_admin(): {}".format(e))
        return {
            "success": None,
            "err": 'Exception: FleetDataCollection: user_is_active_admin(): {}'.format(e),
        }

# Create your views here.
class HomePageView(TemplateView):
    template_name = 'FleetDataCollection.template.home.html'
    client_is_admin = False

    def get_context_data(self, **kwargs):
        try:
            ## Call the base implementation first to get a context
            context = super().get_context_data(**kwargs)
            self.client_is_admin = user_is_active_admin(self.request.user)["success"]
            context["client_is_admin"] = self.client_is_admin
            return context
        except Exception as e:
            context["client_is_admin"] = False
            return context

class AboutPageView(TemplateView):
    template_name = 'FleetDataCollection.template.about.html'

class ContactPageView(TemplateView):
    template_name = 'FleetDataCollection.template.contact.html'

class DriverAndTypeAssignmentConfirmationPageView(generic.ListView):
    template_name = 'FleetDataCollection.template.driverandtypeconfirmation.html'
    context_object_name = 'driver_type_assigment_entries'

    req_success = False
    err_msg = ""

    client_is_admin = False

    def get_queryset(self):
        ## Check for Active Admins
        is_active_admin = user_is_active_admin(self.request.user)
        if is_active_admin["success"] == True:
            self.client_is_admin = True
        else:
            self.req_success = False

        ## Get the core data
        try:
            if self.client_is_admin:
                driver_type_assigment_entries = M5DriverVehicleDataConfirmations.objects.using('FleetDataCollection').all().order_by('unit_number')
            else:
                driver_type_assigment_entries = M5DriverVehicleDataConfirmations.objects.using('FleetDataCollection').all().order_by('unit_number')
                #TODO File this thing by domicile related to user # driver_type_assigment_entries = M5DriverVehicleDataConfirmations.filter().order_by('unit_number')
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: DriverAndTypeAssignmentConfirmationPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return M5DriverVehicleDataConfirmations.objects.none()

        self.req_success = True
        return driver_type_assigment_entries

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