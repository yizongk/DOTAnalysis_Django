from django.shortcuts import render
from django.views.generic import TemplateView

# Create your views here.
class HomePageView(TemplateView):
    template_name = 'LookupTableManager.template.home.html'
    client_is_admin = False

    def get_context_data(self, **kwargs):
        try:
            ## Call the base implementation first to get a context
            context = super().get_context_data(**kwargs)
            # self.client_is_admin = user_is_active_admin(self.request.user)["isAdmin"]
            context["client_is_admin"] = self.client_is_admin
            return context
        except Exception as e:
            context["client_is_admin"] = False
            return context


class AboutPageView(TemplateView):
    template_name = 'LookupTableManager.template.about.html'


class ContactPageView(TemplateView):
    template_name = 'LookupTableManager.template.contact.html'


# Abrar- class for the AG-Grid
###########################################################################################################################################################

from .models import WUTable2
import json
from django.views.generic import ListView
from django.core.serializers.json import DjangoJSONEncoder

def get_active_emp_qryset(
    fields_list = [
    'wu'
    ,'div'
    ,'workunitdescription'
    ,'divisiongroup'
    ,'subdivision'
    ]):
    qryset = WUTable2.objects.using('LookupTableManager').all()
    return qryset.values(*fields_list) #returns a <QuerySet [{;wu;: '1000', 'div': 'Executive', 'workunitdescription': ...}]
    #works fine 

class LookUpView(ListView):
    # Workunit = None
    # queryset = WUTable2.objects.all()
    model = WUTable2
    template_name = 'LookupTableManager.template.table.html'
    context_object_name = 'Workunit'
    Workunit = None
    def get_queryset(self):
        columnDefs = [
            {'headerName': 'WU', 'field': 'wu'}
            ,{'headerName': 'DIV', 'field': 'div'}
            ,{'headerName': 'WorkUnitDescription', 'field': 'workunitdescription'}
            ,{'headerName': 'DivisionGroup', 'field': 'divisiongroup'}
            ,{'headerName': 'SubDivision', 'field': 'subdivision'}
        ]
        fields_list = [each['field'] for each in columnDefs]
        Workunit = get_active_emp_qryset(fields_list= fields_list)
        self.Workunit = json.dumps(list(Workunit), cls=DjangoJSONEncoder)
        # return {'columnDefs': self.Workunit}


    def get_context_data(self,**kwargs):
        columnDefs = [
            {'headerName': 'WU', 'field': 'wu'}
            ,{'headerName': 'DIV', 'field': 'div'}
            ,{'headerName': 'WorkUnitDescription', 'field': 'workunitdescription'}
            ,{'headerName': 'DivisionGroup', 'field': 'divisiongroup'}
            ,{'headerName': 'SubDivision', 'field': 'subdivision'}
        ]
        context = super().get_context_data(**kwargs)
        context["Workunit"] = self.Workunit
        context["columnDefs"] = columnDefs
        return {'datadisplay': context["Workunit"], 'columnDefs': context["columnDefs"]}

###########################################################################################################################################################