from django.shortcuts import render
from django.views.generic import TemplateView
from django.views import generic
from django.http import HttpResponse, JsonResponse
from .models import *
from django.db.models import Min, Q
import json


## Check if remote user is admin and is active
def user_is_active_admin(username):
    try:
        admin_query = TblAdmins.objects.using('OrgChartWrite').filter(
            windows_username=username,
            active=True, ## Filters for active Admins
        )
        if admin_query.count() > 0:
            return {
                "isAdmin": True,
                "err": "",
            }
        return {
            "isAdmin": False,
            "err": '{} is not an active Admin'.format(username),
        }
    except Exception as e:
        print("Exception: user_is_active_admin(): {}".format(e))
        return {
            "isAdmin": None,
            "err": 'Exception: user_is_active_admin(): {}'.format(e),
        }


# Create your views here.
class HomePageView(TemplateView):
    template_name = 'OrgChartPortal.template.home.html'
    client_is_admin = False

    def get_context_data(self, **kwargs):
        try:
            ## Call the base implementation first to get a context
            context = super().get_context_data(**kwargs)
            self.client_is_admin = user_is_active_admin(self.request.user)["isAdmin"]
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
        wu_query = TblPermissions.objects.using('OrgChartRead').filter(
            windows_username=username,
        ).order_by('wu')

        if wu_query.count() > 0:
            return {
                "success": True,
                "err": "",
                "wu_list": [each.wu.wu for each in wu_query],
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

    ## TODO Implement Admin in database
    # def get_queryset(self):
    #     ## Check for Active Admins
    #     # is_active_admin = user_is_active_admin(self.request.user)
    #     # if is_active_admin["success"] == True:
    #     #     self.client_is_admin = True
    #     # else:
    #     #     self.req_success = False

    #     ## Get the core data
    #     try:
    #         if self.client_is_admin:
    #             pms_entries = TblEmployees.objects.using('OrgChartRead').all().order_by('wu')
    #         else:
    #             allowed_wu_list_obj = get_allowed_list_of_wu(self.request.user)
    #             if allowed_wu_list_obj['success'] == False:
    #                 raise ValueError(f"get_allowed_list_of_wu() failed: {allowed_wu_list_obj['err']}")
    #             else:
    #                 allowed_wu_list = allowed_wu_list_obj['wu_list']

    #             pms_entries = TblEmployees.objects.using('OrgChartRead').filter(
    #                 wu__in=allowed_wu_list,
    #             ).order_by('wu')
    #     except Exception as e:
    #         self.req_success = False
    #         self.err_msg = "Exception: EmpGridPageView(): get_queryset(): {}".format(e)
    #         print(self.err_msg)
    #         return TblEmployees.objects.none()

    #     self.req_success = True
    #     return pms_entries

    def get_queryset(self):
        ## Check for Active Admins
        # is_active_admin = user_is_active_admin(self.request.user)
        # if is_active_admin["success"] == True:
        #     self.client_is_admin = True
        # else:
        #     self.client_is_admin = False

        ## Get the core data
        try:
            if self.client_is_admin:
                emp_entries = TblEmployees.objects.using('OrgChartRead').all().order_by('wu')
            else:
                allowed_wu_list_obj = get_allowed_list_of_wu(self.request.user)
                if allowed_wu_list_obj['success'] == False:
                    raise ValueError(f"get_allowed_list_of_wu() failed: {allowed_wu_list_obj['err']}")
                else:
                    allowed_wu_list = allowed_wu_list_obj['wu_list']

                emp_entries = TblEmployees.objects.using('OrgChartRead').filter(
                    pms__wu__in=allowed_wu_list,
                ).order_by('pms__wu')
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: EmpGridPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return None

        self.req_success = True
        return emp_entries

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


def GetClientWUPermissions(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: OrgChartPortal: GetClientWUPermissions(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetClientWUPermissions():\n\nUNAUTHENTICATE USER!",
        })

    ## Get the data
    try:
        wu_permissions_query = TblPermissions.objects.using('OrgChartRead').filter(
                windows_username=remote_user
            ).order_by('wu__wu')

        wu_permissions_list_json = list(wu_permissions_query.values('wu__wu', 'wu__wu_desc', 'wu__subdiv'))

        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": wu_permissions_list_json,
        })
    except Exception as e:
        err_msg = "Exception: OrgChartPortal: GetClientWUPermissions(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })


def GetClientTeammates(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: OrgChartPortal: GetClientTeammates(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetClientTeammates():\n\nUNAUTHENTICATE USER!",
        })

    ## Get the data
    try:
        wu_permissions_query = TblPermissions.objects.using('OrgChartRead').filter(
                windows_username=remote_user
            ).order_by('wu__wu')

        wu_permissions_list_json = wu_permissions_query.values('wu__wu')

        teammates_query = TblPermissions.objects.using('OrgChartRead').filter(
                wu__wu__in=wu_permissions_list_json
            ).order_by('pms__pms')

        teammates_list_json = list(teammates_query.values('pms__pms').annotate(pms__first_name=Min('pms__first_name'), pms__last_name=Min('pms__last_name')))

        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": teammates_list_json,
        })
    except Exception as e:
        err_msg = "Exception: OrgChartPortal: GetClientTeammates(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })


def GetEmpGridStats(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: OrgChartPortal: GetEmpGridStats(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetEmpGridStats():\n\nUNAUTHENTICATE USER!",
        })

    ## Get the data
    try:
        # teammates_list_json = list(teammates_query.values('pms__pms').annotate(pms__first_name=Min('pms__first_name'), pms__last_name=Min('pms__last_name')))

        allowed_wu_list_obj = get_allowed_list_of_wu(remote_user)
        if allowed_wu_list_obj['success'] == False:
            raise ValueError(f"get_allowed_list_of_wu() failed: {allowed_wu_list_obj['err']}")
        else:
            allowed_wu_list = allowed_wu_list_obj['wu_list']

        client_orgchart_data = TblEmployees.objects.using('OrgChartRead').filter(
            wu__in=allowed_wu_list,
        ).order_by('wu')

        emp_grid_stats_list_json = list(client_orgchart_data.values('pms').annotate(pms__first_name=Min('first_name'), pms__last_name=Min('last_name')))














        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": emp_grid_stats_list_json,
        })
    except Exception as e:
        err_msg = "Exception: OrgChartPortal: GetEmpGridStats(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })


class OrgChartPageView(generic.ListView):
    template_name = 'OrgChartPortal.template.orgchart.html'
    context_object_name = 'emp_entries'

    req_success = False
    err_msg = ""

    client_is_admin = False

    def get_queryset(self):
        ## Check for Active Admins
        is_active_admin = user_is_active_admin(self.request.user)
        if is_active_admin["isAdmin"] == True:
            self.client_is_admin = True
        else:
            self.client_is_admin = False

        ## Get the core data
        try:
            if self.client_is_admin == False:
                return None
            # # emp_entries = TblEmployees.objects.using('OrgChartRead').all().order_by('wu')
            # if self.client_is_admin:
            #     emp_entries = TblEmployees.objects.using('OrgChartRead').all().order_by('wu')
            # else:
            #     allowed_wu_list_obj = get_allowed_list_of_wu(self.request.user)
            #     if allowed_wu_list_obj['success'] == False:
            #         raise ValueError('get_allowed_list_of_wu() failed: {}'.format(allowed_wu_list_obj['err']))
            #     else:
            #         allowed_wu_list = allowed_wu_list_obj['wu_list']

            #     emp_entries = TblEmployees.objects.using('OrgChartRead').filter(
            #         pms__wu__in=allowed_wu_list,
            #     ).order_by('pms__wu')
            emp_entries =  None
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: EmpGridPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return None

        self.req_success = True
        return emp_entries

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


def GetEmpJson(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: OrgChartPortal: GetEmpJson(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetEmpJson():\n\nUNAUTHENTICATE USER!",
        })


    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetEmpJson():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    ## Get the data
    try:
        ## Check for Active Admins
        is_admin = user_is_active_admin(remote_user)["isAdmin"]
        if not is_admin:
            raise ValueError(f"'{remote_user}' is not admin. Only admins can access the GetEmpJson() api")


        active_lv_list = ['B', 'C', 'K', 'M', 'N', 'Q', 'R', 'S']
        root_pms = json_blob['root_pms']

        allowed_wu_list_obj = get_allowed_list_of_wu(remote_user)
        if allowed_wu_list_obj['success'] == False:
            raise ValueError(f"get_allowed_list_of_wu() failed: {allowed_wu_list_obj['err']}")
        else:
            allowed_wu_list = allowed_wu_list_obj['wu_list']

        emp_data = TblEmployees.objects.using('OrgChartRead').filter(
            wu__in=allowed_wu_list,
        ).exclude(
           Q(supervisor_pms__isnull=True) | Q(supervisor_pms__exact='')
           ,~Q(pms__exact=root_pms)
        ).filter(
            lv__in=active_lv_list
        ).order_by(
            'supervisor_pms'
        )

        """
            ## Build a dict of emp pms and a dict of its emp info
            ##  {
            ##      "1234566":
            ##          {
            ##              "pms":              "1234567"
            ##              "last_name":        "john"
            ##              "first_name":       "doe"
            ##              "supervisor_pms":   "7654321"
            ##          }
            ##      ,"7654321": {...}
            ##      .
            ##      .
            ##      .
            ##  }
            flat_emp_dict = {}
            for each in emp_data:
                each_emp_dict = {}
                each_emp_dict[f"pms"] = f"{each.pms}".strip()
                each_emp_dict[f"last_name"] = f"{each.last_name}".strip()
                each_emp_dict[f"first_name"] = f"{each.first_name}".strip()
                try:
                    each_emp_dict[f"supervisor_pms"] = f"{each.supervisor_pms}".strip()
                except TblEmployees.DoesNotExist:
                    each_emp_dict[f"supervisor_pms"] = None

                flat_emp_dict[ f"{each.pms}".strip() ] = each_emp_dict
        """






        ## Build a dict of Supervisor PMS and its underlings
        ##  {
        ##      "1234567": { # Supervisor PMS
        ##          "pms":              "1234567"
        ##          "last_name":        "obama"
        ##          "first_name":       "barack"
        ##          "lv":               "b"
        ##          "children": [
        ##              {        # Underling number 1
        ##                  "child_pms":              "1155667"
        ##                  "child_last_name":        "john"
        ##                  "child_first_name":       "doe"
        ##                  "child_lv":               "b"
        ##                  "child_supervisor_pms":   "1234567"
        ##              },
        ##              {        # Underling number 2
        ##                  "child_pms":              "2223333"
        ##                  "child_last_name":        "macy"
        ##                  "child_first_name":       "doe"
        ##                  "child_lv":               "b"
        ##                  "child_supervisor_pms":   "1234567"
        ##              },
        ##          ]
        ##      },
        ##      "7654321": {...}
        ##      .
        ##      .
        ##      .
        ##  }
        flat_supervisor_dict = {}
        for each in emp_data:
            ## Can skip if current emp is the root_pms, we don't need any supervisor information of the root
            if each.pms == root_pms:
                continue

            try:
                sup_pms = f"{each.supervisor_pms.pms}".strip()
            except TblEmployees.DoesNotExist:
                sup_pms = None

            # Create supervisor object if it doesn't exists in the dict, creating the child list to store all the child objs
            if sup_pms not in flat_supervisor_dict:
                try:
                    sup_last_name = f"{each.supervisor_pms.last_name}".strip()
                except TblEmployees.DoesNotExist:
                    sup_last_name = None
                try:
                    sup_first_name = f"{each.supervisor_pms.first_name}".strip()
                except TblEmployees.DoesNotExist:
                    sup_first_name = None
                try:
                    sup_lv = f"{each.supervisor_pms.lv}".strip()
                except TblEmployees.DoesNotExist:
                    sup_lv = None

                flat_supervisor_dict[sup_pms] = {
                    "pms":          sup_pms,
                    "last_name":    sup_last_name,
                    "first_name":   sup_first_name,
                    "lv":           sup_lv,
                    "children":        []
                }


            ## Constructing the child object
            each_emp_obj = {}

            try:
                pms = f"{each.pms}".strip()
            except TblEmployees.DoesNotExist:
                pms = None
            try:
                last_name = f"{each.last_name}".strip()
            except TblEmployees.DoesNotExist:
                last_name = None
            try:
                first_name = f"{each.first_name}".strip()
            except TblEmployees.DoesNotExist:
                first_name = None
            try:
                lv = f"{each.lv}".strip()
            except TblEmployees.DoesNotExist:
                lv = None


            each_emp_obj["child_pms"]            = pms
            each_emp_obj["child_last_name"]      = last_name
            each_emp_obj["child_first_name"]     = first_name
            each_emp_obj["child_lv"]             = lv
            each_emp_obj["child_supervisor_pms"] = sup_pms



            flat_supervisor_dict[sup_pms]["children"].append(each_emp_obj)

        ## Build a nested tree dict given a root_node
        ##  {
        ##      "1234567": { # Root node
        ##          "id":               "rootNode"
        ##          "className":        "top-level"
        ##          "pms":              "1234567"
        ##          "last_name":        "obama"
        ##          "first_name":       "barack"
        ##          "lv":               "B"
        ##          "relationship":     "001"
        ##          "children": [
        ##              {        # Underling number 1
        ##                  "pms":              "1155667"
        ##                  "last_name":        "john"
        ##                  "first_name":       "doe"
        ##                  "lv":               "B"
        ##                  "relationship":     "111"
        ##                  "children": [
        ##                      {...},
        ##                      {...}
        ##                  ]
        ##              },
        ##              {        # Underling number 2
        ##                  "pms":              "2223333"
        ##                  "last_name":        "macy"
        ##                  "first_name":       "doe"
        ##                  "lv":               "L"
        ##                  "relationship":     "110"
        ##                  "children": [...]
        ##              },
        ##              {...}
        ##          ]
        ##      }
        ##  }
        ##
        ## Note:
        ##  * relationship Value is a string composed of three "0/1" identifier.
        ##      First character stands for wether current node has parent node;
        ##      Scond character stands for wether current node has siblings nodes;
        ##      Third character stands for wether current node has children node.
        ##      For example: the Root Node should be "relationship": "001", since it has no parent, no sibling and happens to have childs
        ##
        ##  * id Value
        ##      It's a optional property which will be used as id attribute of node
        ##      and data-parent attribute, which contains the id of the parent node
        ##
        ##  For more: https://github.com/dabeng/OrgChart
        ## Returns a child dict obj for a specific node, will contains all sub-childs as well
        #   Assums cur_node is an active emp in the lv status of ('B', 'C', 'K', 'M', 'N', 'Q', 'R', 'S')
        def ChildTreeTraverser(cur_node, cur_node_sibling_count, cur_itr_count, max_itr_count):
            ## Build the relationship val for the current node
            cur_node_is_supervisor = cur_node["pms"] in flat_supervisor_dict

            # cur_node always have a parent
            relationship_val = "1"
            # If cur_node has sibling(s), by checking parent
            if cur_node_sibling_count > 1:
                relationship_val += "1"
            else:
                relationship_val += "0"
            # If cur_node has child(s). In other word he/she is supervisor.
            # Note: If current iteration is last iteration, will mean no child for cur_node.
            if cur_node_is_supervisor and cur_itr_count <= max_itr_count:
                relationship_val += "1"
            else:
                relationship_val += "0"


            final_node = {
                "pms":              cur_node["pms"],
                "last_name":        cur_node["last_name"],
                "first_name":       cur_node["first_name"],
                "lv":               cur_node["lv"],
                "relationship":     relationship_val,
                "title":            f"{cur_node['last_name']}, {cur_node['first_name']}",
                "content":          "child\nblah blah",
                "children":         [],
            }

            # To avoid self reference loop where some employee is their own supervisor
            if cur_itr_count > max_itr_count:
                return final_node

            # If cur node is not supervisor, it has no child to keep calling ChildTreeTraverser()
            if not cur_node_is_supervisor:
                return final_node

            # At this point, we assume cur_node is a supervisor and will have child data
            cur_node_with_sup_info = flat_supervisor_dict[cur_node["pms"]]
            # Count only if child is an active emp
            cur_node_child_count = sum(1 for each in cur_node_with_sup_info["children"] if each["child_lv"] in active_lv_list)

            for child in cur_node_with_sup_info["children"]:
                child_of_cur_node_info = {
                    "pms":              child["child_pms"],
                    "last_name":        child["child_last_name"],
                    "first_name":       child["child_first_name"],
                    "lv":               child["child_lv"],
                }

                # Child must be active emp to keep calling ChildTreeTraverser()
                if child_of_cur_node_info["lv"] in active_lv_list:
                    child_final = ChildTreeTraverser(cur_node=child_of_cur_node_info, cur_node_sibling_count=cur_node_child_count, cur_itr_count=cur_itr_count+1, max_itr_count=max_itr_count)
                    final_node["children"].append(child_final)

            return final_node



        root_emp_obj = flat_supervisor_dict[root_pms]
        # Count only if child is an active emp
        root_child_count = sum(1 for each in root_emp_obj["children"] if each["child_lv"] in active_lv_list)

        tree_supervisor_dict = {
            "id":           "rootNode",
            "className":    "top-level",
            "pms":          root_emp_obj["pms"],
            "last_name":    root_emp_obj["last_name"],
            "first_name":   root_emp_obj["first_name"],
            "lv":           root_emp_obj["lv"],
            "relationship": "001",
            "title": f"{root_emp_obj['last_name']}, {root_emp_obj['first_name']}",
            "content": "root\nblah blah",
            "children":        [],
        }

        ## Build the child nodes to append to current node, and call ChildTreeTraverser() on each of the child node
        for child in root_emp_obj["children"]:
            child_of_cur_node_info = {
                "pms":              child["child_pms"],
                "last_name":        child["child_last_name"],
                "first_name":       child["child_first_name"],
                "lv":               child["child_lv"],
            }

            # Child must be active emp to start ChildTreeTraverser(). ChildTreeTraverser() Assumes cur_node is an active employee
            if child_of_cur_node_info["lv"] in active_lv_list:
                child_final = ChildTreeTraverser(cur_node=child_of_cur_node_info, cur_node_sibling_count=root_child_count, cur_itr_count=0, max_itr_count=9)
                tree_supervisor_dict["children"].append(child_final)



        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": tree_supervisor_dict,
        })
    except Exception as e:
        err_msg = "Exception: OrgChartPortal: GetEmpJson(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })


def GetEmpCsv(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: OrgChartPortal: GetEmpCsv(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetEmpCsv():\n\nUNAUTHENTICATE USER!",
        })

    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetEmpCsv():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    ## Get the data
    try:
        ## Check for Active Admins
        is_admin = user_is_active_admin(remote_user)["isAdmin"]
        if not is_admin:
            raise ValueError("'{}' is not admin. Only admins can access the GetEmpCsv() api".format(remote_user))


        active_lv_list = ['B', 'C', 'K', 'M', 'N', 'Q', 'R', 'S']
        root_pms = json_blob['root_pms']

        allowed_wu_list_obj = get_allowed_list_of_wu(remote_user)
        if allowed_wu_list_obj['success'] == False:
            raise ValueError('get_allowed_list_of_wu() failed: {}'.format(allowed_wu_list_obj['err']))
        else:
            allowed_wu_list = allowed_wu_list_obj['wu_list']

        emp_data = TblEmployees.objects.using(
            'OrgChartRead'
        ).filter(
            Q(wu__in=allowed_wu_list)
        ).exclude(
            Q(supervisor_pms__isnull=True) | Q(supervisor_pms__exact='')
            ,~Q(pms__exact=root_pms) # our very top root_pms will have a null supervisor_pms, so this condition is to include the top root_pms despite the first exclude condition
        ).filter(
            lv__in=active_lv_list
        ).order_by(
            'supervisor_pms'
        )


        ## Build a dict of emp pms and a dict of its emp info
        ##  {
        ##      "1234566":
        ##          {
        ##              "pms":              "1234567"
        ##              "last_name":        "john"
        ##              "first_name":       "doe"
        ##              "supervisor_pms":   "7654321"
        ##          }
        ##      ,"7654321": {...}
        ##      .
        ##      .
        ##      .
        ##  }
        flat_query_dict = emp_data.values( # Returns a query set that returns dicts. MUCH faster than going though emp_data in a for loop (53 secs down to 350ms).
            "pms"
            ,"last_name"
            ,"first_name"
            ,"office_title"
            ,"civil_title"
            ,"wu__wu_desc"
            ,"supervisor_pms"
        )

        flat_emp_dict = {}
        for each in flat_query_dict:
            each_emp_dict = {}

            each_emp_dict[f"pms"]               = f"{each['pms']}".strip()
            each_emp_dict[f"last_name"]         = f"{each['last_name']}".strip()
            each_emp_dict[f"first_name"]        = f"{each['first_name']}".strip()
            each_emp_dict[f"office_title"]      = f"{each['office_title']}".strip()
            each_emp_dict[f"civil_title"]       = f"{each['civil_title']}".strip()
            each_emp_dict[f"wu_desc"]           = f"{each['wu__wu_desc']}".strip()
            each_emp_dict[f"supervisor_pms"]    = f"{each['supervisor_pms']}".strip()

            flat_emp_dict[f"{each['pms']}".strip()] = each_emp_dict


        def CanReachRoot(pms):
            ## pms is root_pms, so lineage is reachable to root_pms, return true
            if pms == root_pms:
                return True

            ## pms is a root that's not root_pms, so lineage is not reachable to root_pms, return false
            if pms == '' or pms is None:
                return False

            ## pms is not a root, check its parent
            try:
                parent_pms = flat_emp_dict[pms]['supervisor_pms']
            except KeyError:
                parent_pms = None
            return CanReachRoot( parent_pms )


        ## Filter for only the root_pms and its childs
        flat_emp_under_root_dict = {}
        for emp_pms in flat_emp_dict:
            emp = flat_emp_dict[emp_pms]
            if CanReachRoot( emp['pms'] ):
                flat_emp_under_root_dict[ emp['pms'] ] = emp



        import csv
        from io import StringIO
        dummy_in_mem_file = StringIO()

        ## Create the csv
        writer = csv.writer(dummy_in_mem_file)
        writer.writerow(["pms", "sup_pms", "last_name", "first_name", "office_title", "civil_title", "wu_desc"]) # For reference to what to name your id and parent id column: https://github.com/bumbeishvili/org-chart/issues/88
        # writer.writerow(["last_name", "first_name", "id", "parentId"])

        for each in flat_emp_under_root_dict:
            try:
                ## In the case that root_pms is not the actual top root of the entire org tree, but it's a middle node somewhere, we need to set that emp's sup_pms to empty string
                if flat_emp_under_root_dict[each]['pms'] == root_pms:
                    sup_pms = ""
                else:
                    sup_pms = flat_emp_under_root_dict[each]['supervisor_pms']
            except TblEmployees.DoesNotExist:
                sup_pms = ""

            eachrow = [
                flat_emp_under_root_dict[each]['pms']
                ,sup_pms
                ,flat_emp_under_root_dict[each]['last_name']
                ,flat_emp_under_root_dict[each]['first_name']
                ,flat_emp_under_root_dict[each]['office_title']
                ,flat_emp_under_root_dict[each]['civil_title']
                ,flat_emp_under_root_dict[each]['wu_desc']
            ]
            writer.writerow(eachrow)


        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": dummy_in_mem_file.getvalue(),
        })
    except Exception as e:
        err_msg = "Exception: OrgChartPortal: GetEmpCsv(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })


def GetCommissionerPMS(request):
    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: OrgChartPortal: GetCommissionerPMS(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetCommissionerPMS():\n\nUNAUTHENTICATE USER!",
        })


    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "OrgChartPortal: GetCommissionerPMS():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    ## Get the data
    try:
        ## Check for Active Admins
        is_admin = user_is_active_admin(remote_user)["isAdmin"]
        if not is_admin:
            raise ValueError("'{}' is not admin. Only admins can access the GetCommissionerPMS() api".format(remote_user))


        from PMU_DjangoWebApps.secret_settings import OrgChartRootPMS

        emp_data = TblEmployees.objects.using('OrgChartRead').filter(
            pms__exact=f'{OrgChartRootPMS}',
        ).first()

        pms = emp_data.pms

        return JsonResponse({
            "post_success": True,
            "post_msg": None,
            "post_data": pms,
        })
    except Exception as e:
        err_msg = "Exception: OrgChartPortal: GetCommissionerPMS(): {}".format(e)
        print(err_msg)
        return JsonResponse({
            "post_success": False,
            "post_msg": err_msg
        })

