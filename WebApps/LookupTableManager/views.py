from django.views.generic import TemplateView
from django.core.exceptions import ObjectDoesNotExist
from .models import *
import json
from django.views.generic import ListView
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse


def user_is_active_admin(username=None): #User Authentication
    try:
        admin_query = TblUsers.objects.using('LookupTableManager').filter(
            windows_username=username,
            is_admin=True,
        )
        if admin_query.count() > 0:
            return True
        else:
            return False
    except Exception as e:
       raise ValueError(f"user_is_active_admin(): {e}")


def get_active_emp_qryset(
    fields_list = [
        'wu'
        ,'div'
        ,'wu_desc'
        ,'div_group'
        ,'subdiv'
        , 'active'
        ]):
        qryset = TblWorkUnits.objects.using('LookupTableManager').all()
        return qryset.values(*fields_list) #returns a <QuerySet [{;wu;: '1000', 'div': 'Executive', 'workunitdescription': ...}]


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


class LookUpView(ListView):
    # queryset = TblWorkUnits.objects.all()
    model = TblWorkUnits
    template_name = 'LookupTableManager.template.table.html'
    context_object_name = 'Workunit'
    Workunit = None

    req_success = False
    err_msg = ""
    client_is_admin = False

    def get_queryset(self):
        self.client_is_admin = user_is_active_admin(self.request.user)
        try:
            if not self.client_is_admin:
                raise ValueError("'{}' is not an Admin, and is not authorized to see this page.".format(self.request.user))
            else:
                columnDefs = [
                    {'headerName': 'WU', 'field': 'wu'}
                    ,{'headerName': 'DIV', 'field': 'div'}
                    ,{'headerName': 'WorkUnitDescription', 'field': 'wu_desc'}
                    ,{'headerName': 'DivisionGroup', 'field': 'div_group'}
                    ,{'headerName': 'SubDivision', 'field': 'subdiv'}
                    ,{'headerName': 'Active', 'field': 'active'}
                    ]
                fields_list = [each['field'] for each in columnDefs]
                Workunit = get_active_emp_qryset(fields_list= fields_list)
                self.Workunit = json.dumps(list(Workunit), cls=DjangoJSONEncoder)
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: AdminPanelPageView(): get_queryset(): {}".format(e)
            return None

        self.req_success = True
        return None

    def get_context_data(self,**kwargs):
        try:
            columnDefs = [
                {'headerName': 'WU', 'field': 'wu'}
                ,{'headerName': 'DIV', 'field': 'div'}
                ,{'headerName': 'WorkUnitDescription', 'field': 'wu_desc'}
                ,{'headerName': 'DivisionGroup', 'field': 'div_group'}
                ,{'headerName': 'SubDivision', 'field': 'subdiv'}
                ,{'headerName': 'Active', 'field': 'active'}
            ]
            context                         = super().get_context_data(**kwargs)
            context["req_success"]          = self.req_success
            context["err_msg"]              = self.err_msg
            context["client_is_admin"]      = self.client_is_admin

            context["Workunit"]             = self.Workunit
            context["columnDefs"]           = columnDefs
            return{'datadisplay': context["Workunit"], 'columnDefs': context["columnDefs"], 'req_success':context["req_success"], 'err_msg':context["err_msg"], 'client_is_admin':context["client_is_admin"]}
        except Exception as e:
            self.req_success = False
            self.err_msg ="Exception: Table: get_queryset(): {}".format(e)
            context                         = super().get_context_data(**kwargs)
            context["client_is_admin"]      = False
            context["req_success"]          = self.req_success
            context["err_msg"]              = self.err_msg
            return context


def UpdateWU(request): #UPDATE API
    """
    Return a json response in this format. My front end error handling works with this format.
    {
        "post_success"  : ...       # Must have. Set this to True if the data was saved to the database successfully, else return False. When set to False, the front end will display the content in @post_msg.
        ,"post_msg"     : ...       # Must have. Set this to any error messages that happens, else set it to None. This variable's content will be display to the front end if @post_success is set to False.
        ,"post_data"    : ...       # Must have. Set this to anything that you want to sent back to the front end. I usually set this to the row of data that was just updated, to be used to update AG Grid on the front end when @post_success is set to True.
        ,"...": ...                 # Optional.  Additional variables to return to the front-end
    }
    """

    if request.method != "POST":
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"{request.method} HTTP request not supported",
        })
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: UpdateWU(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : "UpdateWU():\n\nUNAUTHENTICATE USER!",
            "post_data"     : None,
        })
    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"LookupTableManager: UpdateWU():\n\n Unable to load request.body as a json object: {e}",
        })
    try:
        WUvariable      = json_blob['wu']
        column_name     = json_blob['column_name']
        new_value       = json_blob['new_value']
        if WUvariable is None or WUvariable == '':
            raise ValueError(f"wu: '{WUvariable}' cannot be None or Empty string")
        if column_name is None or column_name == '':
            raise ValueError(f"column_name: '{column_name}' cannot be None or Empty string")
        if new_value is None or new_value == '':
            raise ValueError(f"new_value: '{new_value}' cannot be None or Empty string")
        ## Data validation
        valid_editable_col = {
            'DIV': 'div'
            ,'WorkUnitDescription': 'wu_desc'
            , 'DivisionGroup': 'div_group'
            , 'SubDivision': 'subdiv'
            , 'Active': 'active'
        }
        if column_name not in list(valid_editable_col.keys()):
            raise ValueError(f"column_name '{column_name}' is not a valid editable column")
        # Check for Approved Admins
        is_admin = user_is_active_admin(remote_user)
        if  is_admin == False:
            raise ValueError(f"'{remote_user}' is not an Approved Admin and cannot use this Update API")
        try:
            workunit = TblWorkUnits.objects.using('LookupTableManager').get(wu = WUvariable)
        except ObjectDoesNotExist as e:
            raise ValueError(f"Cannot find Work Unit record with '{WUvariable}'")
        else:
            ## Set the data to the specific column
            if column_name == 'DIV':
                workunit.div = new_value
            elif column_name == 'WorkUnitDescription':
                workunit.wu_desc = new_value
            elif column_name == 'DivisionGroup':
                workunit.div_group = new_value
            elif column_name == 'SubDivision':
                workunit.subdiv = new_value
            elif column_name == 'Active':
                workunit.active = new_value
            workunit.save(using= 'LookupTableManager')
        return JsonResponse({
            "post_success"  : True,
            "post_msg"      : None,
            "post_data"     : {
                'wu': WUvariable
                ,'column_name': valid_editable_col[column_name]
                ,'new_value': new_value
            },
        })
    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"LookupTableManager: UpdateWU():\n\nError: {e}",
        })