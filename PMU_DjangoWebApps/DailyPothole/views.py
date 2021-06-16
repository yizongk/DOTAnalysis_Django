from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import generic

# Create your views here.
class HomePageView(TemplateView):
    template_name = 'DailyPothole.template.home.html'
    client_is_admin = False

    def get_context_data(self, **kwargs):
        try:
            ## Call the base implementation first to get a context
            context = super().get_context_data(**kwargs)
            # self.client_is_admin = user_is_active_admin(self.request.user)["success"]
            # context["client_is_admin"] = self.client_is_admin
            return context
        except Exception as e:
            # context["client_is_admin"] = False
            return context

class AboutPageView(TemplateView):
    template_name = 'DailyPothole.template.about.html'

class ContactPageView(TemplateView):
    template_name = 'DailyPothole.template.contact.html'

class DataCollectionPageView(generic.ListView):
    template_name = 'DailyPothole.template.datacollection.html'
    context_object_name = 'pothole_data'

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
                # pothole_data = M5DriverVehicleDataConfirmations.objects.using('FleetDataCollection').all().order_by('unit_number')
                pothole_data = None
            else:
                # allowed_unit_number_list_obj = get_allowed_list_of_unit_numbers(self.request.user)
                # if allowed_unit_number_list_obj['success'] == False:
                #     raise ValueError('get_allowed_list_of_unit_numbers() failed: {}'.format(allowed_unit_number_list_obj['err']))
                # else:
                #     allowed_unit_number_list = allowed_unit_number_list_obj['unit_number_list']

                # pothole_data = M5DriverVehicleDataConfirmations.objects.using('FleetDataCollection').filter(
                #     unit_number__in=allowed_unit_number_list,
                # ).order_by('unit_number')
                pothole_data = None
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: DateCollectionPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            # return M5DriverVehicleDataConfirmations.objects.none()
            return None

        self.req_success = True
        return pothole_data

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
