from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from django.views.generic import TemplateView
from django.views import generic
from .models import *
from datetime import datetime
from django.utils import timezone
import pytz ## For converting datetime objects from one timezone to another timezone
from django.db.models import Q
import json
## Create your views here.

def get_admin_category_permissions():
    try:
        user_permissions_list = Category.objects.all()
        return {
            "success": True,
            "pk_list": [x.category_id for x in user_permissions_list],
            "err": '',
            "category_names": [x.category_name for x in user_permissions_list],
        }
    except Exception as e:
        print("Exception: get_user_category_permissions(): {}".format(e))
        return {
            "success": False,
            "err": "Exception: get_user_category_permissions(): {}".format(e),
            "pk_list": [],
            "category_names": [],
        }

def get_user_category_permissions(username):
    try:
        user_permissions_list = UserPermissions.objects.filter(user__login=username)
        return {
            "success": True,
            "pk_list": [x.category.category_id for x in user_permissions_list],
            "err": '',
            "category_names": [x.category.category_name for x in user_permissions_list],
        }
    except Exception as e:
        print("Exception: get_user_category_permissions(): {}".format(e))
        return {
            "success": False,
            "err": "Exception: get_user_category_permissions(): {}".format(e),
            "pk_list": [],
            "category_names": [],
        }

## Check if remote user is admin and is active
def user_is_active_admin(username):
    try:
        admin_query = Admins.objects.filter(
            user__login=username,
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
        print("Exception: user_is_active_admin(): {}".format(e))
        return {
            "success": None,
            "err": 'Exception: user_is_active_admin(): {}'.format(e),
        }

def user_is_active_user(username):
    try:
        user_query = Users.objects.filter(
            login=username,
            active_user=True, ## Filters for active users
        )
        if user_query.count() > 0:
            return {
                "success": True,
                "err": "",
            }
        return {
            "success": False,
            "err": '{} is not an active User or is not registered'.format(username),
        }
    except Exception as e:
        print("Exception: user_is_active_user(): {}".format(e))
        return {
            "success": None,
            "err": 'Exception: user_is_active_user(): {}'.format(e),
        }

## Given a record id, checks if user has permission to edit the record
def user_has_permission_to_edit(username, record_id):
    try:
        is_active_admin = user_is_active_admin(username)
        if is_active_admin["success"] == True:
            category_info = get_admin_category_permissions()
        elif is_active_admin["success"] == False:
            ## If not admin, do standard filter with categories
            category_info = get_user_category_permissions(username)
        elif is_active_admin["success"] is None:
            return {
                    "success": False,
                    "err": "Permission denied: Cannot determine if user is Admin or not: {}".format(is_active_admin["err"]),
                }

        if category_info["success"] == True:
            category_pk_list = category_info["pk_list"]
        elif (category_info["success"] == False) or (category_info["success"] is None):
            return {
                "success": False,
                "err": "Permission denied: user_cat_permissions['success'] has an unrecognized value: {}".format(category_info['err']),
            }
        else:
            return {
                "success": False,
                "err": "Permission denied: user_cat_permissions['success'] has an unrecognized value: {}".format(category_info['success']),
            }

        category_id_permission_list = category_info["pk_list"]
        record_category_info = IndicatorData.objects.values('indicator__category__category_id', 'indicator__category__category_name').get(record_id=record_id) ## Take a look at https://docs.djangoproject.com/en/3.0/ref/models/querysets/ on "values()" section
        record_category_id = record_category_info["indicator__category__category_id"]
        record_category_name = record_category_info["indicator__category__category_name"]
        if len(category_id_permission_list) != 0:
            if record_category_id in category_id_permission_list:
                return {
                    "success": True,
                    "err": "",
                }
            else:
                print( "Permission denied: '{}' does not have permission to edit {} Category.".format(username, record_category_name) )
                return {
                    "success": False,
                    "err": "Permission denied: '{}' does not have permission to edit {} Category.".format(username, record_category_name),
                }
        elif category_info["success"] == False:
            raise ## re-raise the error that happend in get_user_category_permissions(), because ["success"] is only False when an exception happens in get_user_category_permissions()
        else: ## Else successful query, but no permissions results found
            return {
                "success": False,
                "err": "Permission denied: '{}' does not have permission to edit {} Category.".format(username, record_category_name),
            }

        return {
            "success": False,
            "err": "Permission denied: '{}' does not have permission to edit {} Category.".format(username, record_category_name),
        }
    except Exception as e:
        print("Exception: user_has_permission_to_edit(): {}".format(e))
        return {
            "success": None,
            "err": 'Exception: user_has_permission_to_edit(): {}'.format(e),
        }

class HomePageView(TemplateView):
    template_name = 'PerInd.template.home.html'
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
    template_name = 'PerInd.template.about.html'

class ContactPageView(TemplateView):
    template_name = 'PerInd.template.contact.html'

## Method Flowchart (the order of execution) for generic.ListView
##     setup()
##     dispatch()
##     http_method_not_allowed()
##     get_template_names()
##     get_queryset()
##     get_context_object_name()
##     get_context_data()
##     get()
##     render_to_response()
class WebGridPageView(generic.ListView):
    template_name = 'PerInd.template.webgrid.html'
    context_object_name = 'indicator_data_entries'

    req_success = False
    category_permissions = []
    err_msg = ""

    paginate_by = 12

    req_sort_dir = ""
    req_sort_by = ""

    uniq_titles = []
    uniq_years = []
    uniq_fiscal_years = []
    uniq_months = []
    uniq_categories = []

    req_title_list_filter = []
    req_yr_list_filter = [] ## Calendar Year
    req_mn_list_filter = []
    req_fy_list_filter = [] ## Fiscal Year
    req_cat_list_filter = [] ## Category

    ctx_pagination_param = ""

    title_sort_anchor_GET_param = ""
    yyyy_sort_anchor_GET_param = ""
    mm_sort_anchor_GET_param = ""
    fiscal_year_sort_anchor_GET_param = ""
    cat_sort_anchor_GET_param = ""

    client_is_admin = False

    def get_queryset(self):

        ## Collect GET url parameter info
        temp_sort_dir = self.request.GET.get('SortDir')
        if (temp_sort_dir is not None and temp_sort_dir != '') and (temp_sort_dir == 'asc' or temp_sort_dir == 'desc'):
            self.req_sort_dir = temp_sort_dir

        temp_sort_by = self.request.GET.get('SortBy')
        if (temp_sort_by is not None and temp_sort_by != ''):
            self.req_sort_by = temp_sort_by

        self.req_title_list_filter = self.request.GET.getlist('TitleListFilter')
        self.req_yr_list_filter = self.request.GET.getlist('YYYYListFilter')
        self.req_mn_list_filter = self.request.GET.getlist('MMListFilter')
        self.req_fy_list_filter = self.request.GET.getlist('FiscalYearListFilter')
        self.req_cat_list_filter = self.request.GET.getlist('CategoriesListFilter')

        ## Get authorized list of Categories of Indicator Data, also check for Active Admins or Users
        is_active_admin = user_is_active_admin(self.request.user)
        if is_active_admin["success"] == True:
            self.client_is_admin = True
            user_cat_permissions = get_admin_category_permissions()

        elif is_active_admin["success"] == False:
            self.client_is_admin = False
            is_active_user = user_is_active_user(self.request.user)

            if is_active_user["success"] == True:
                 ## If not admin, do standard filter with categories
                user_cat_permissions = get_user_category_permissions(self.request.user)
            else:
                self.req_success = False
                self.err_msg = "WebGridPageView(): get_queryset(): {}".format(is_active_user["err"])
                print(self.err_msg)
                return IndicatorData.objects.none()

        elif is_active_admin["success"] is None:
            self.req_success = False
            self.err_msg = "Exception: WebGridPageView(): get_queryset(): {}".format(is_active_admin["err"])
            print(self.err_msg)
            return IndicatorData.objects.none()

        if user_cat_permissions["success"] == True:
            category_pk_list = user_cat_permissions["pk_list"]
            self.category_permissions = user_cat_permissions["category_names"]
        elif (user_cat_permissions["success"] == False) or (user_cat_permissions["success"] is None):
            self.req_success = False
            self.err_msg = "Exception: WebGridPageView(): get_queryset(): {}".format(user_cat_permissions['err'])
            print(self.err_msg)
            return IndicatorData.objects.none()
        else:
            self.req_success = False
            self.err_msg = "Exception: WebGridPageView(): get_queryset(): user_cat_permissions['success'] has an unrecognized value: {}".format(user_cat_permissions['success'])
            print(self.err_msg)
            return IndicatorData.objects.none()

        ## Default filters on the WebGrid dataset
        try:
            indicator_data_entries = IndicatorData.objects.filter(
                indicator__category__pk__in=category_pk_list, ## Filters for authorized Categories
                indicator__active=True, ## Filters for active Indicator titles
                year_month__yyyy__gt=timezone.now().year-4, ## Filter for only last four year, "yyyy_gt" is "yyyy greater than"
            )

            indicator_data_entries = indicator_data_entries.exclude(  ## Exclude any future dates greater than current month and current year
                Q(
                    year_month__yyyy__exact=timezone.now().year,
                    year_month__mm__gt=timezone.now().month
                ) |
                Q(
                    year_month__yyyy__gt=timezone.now().year,
                )
            )
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: WebGridPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return IndicatorData.objects.none()

        ## refrencee: https://stackoverflow.com/questions/5956391/django-objects-filter-with-list
        ## Filter dataset from Dropdown list
        ## Filter by Titles
        if len(self.req_title_list_filter) >= 1:
            try:
                qs = Q()
                for i in self.req_title_list_filter:
                    qs = qs | Q(indicator__indicator_title=i)
                indicator_data_entries = indicator_data_entries.filter(qs)
            except Exception as e:
                self.req_success = False
                self.err_msg = "Exception: WebGridPageView(): get_queryset(): Titles Filtering: {}".format(e)
                print(self.err_msg)
                return IndicatorData.objects.none()
        ## Filter by YYYYs
        if len(self.req_yr_list_filter) >= 1:
            try:
                qs = Q()
                for i in self.req_yr_list_filter:
                    qs = qs | Q(year_month__yyyy=i)
                indicator_data_entries = indicator_data_entries.filter(qs)
            except Exception as e:
                self.req_success = False
                self.err_msg = "Exception: WebGridPageView(): get_queryset(): Years Filtering: {}".format(e)
                print(self.err_msg)
                return IndicatorData.objects.none()
        ## Filter by MMs
        if len(self.req_mn_list_filter) >= 1:
            try:
                qs = Q()
                for i in self.req_mn_list_filter:
                    qs = qs | Q(year_month__mm=i)
                indicator_data_entries = indicator_data_entries.filter(qs)
            except Exception as e:
                self.req_success = False
                self.err_msg = "Exception: WebGridPageView(): get_queryset(): Months Filtering: {}".format(e)
                print(self.err_msg)
                return IndicatorData.objects.none()
        ## Filter by Fiscal Years
        if len(self.req_fy_list_filter) >= 1:
            try:
                qs = Q()
                for i in self.req_fy_list_filter:
                    qs = qs | Q(year_month__fiscal_year=i)
                indicator_data_entries = indicator_data_entries.filter(qs)
            except Exception as e:
                self.req_success = False
                self.err_msg = "Exception: WebGridPageView(): get_queryset(): Fiscal Years Filtering: {}".format(e)
                print(self.err_msg)
                return IndicatorData.objects.none()
        ## Filter by Categories
        if self.client_is_admin == True:
            if len(self.req_cat_list_filter) >= 1:
                try:
                    qs = Q()
                    for i in self.req_cat_list_filter:
                        qs = qs | Q(indicator__category__category_name=i)
                    indicator_data_entries = indicator_data_entries.filter(qs)
                except Exception as e:
                    self.req_success = False
                    self.err_msg = "Exception: WebGridPageView(): get_queryset(): Categories Filtering: {}".format(e)
                    print(self.err_msg)
                    return IndicatorData.objects.none()

        ## Sort dataset from sort direction and sort column
        try:
            ## Default sort
            if self.req_sort_by == '':
                indicator_data_entries = indicator_data_entries.order_by('indicator__category__category_name', '-year_month__fiscal_year', '-year_month__mm', 'indicator__indicator_title')
            else:
                if self.req_sort_dir == "asc":
                    indicator_data_entries = indicator_data_entries.order_by(self.req_sort_by)
                elif self.req_sort_dir == "desc":
                    indicator_data_entries = indicator_data_entries.order_by('-{}'.format(self.req_sort_by))
                else:
                    self.req_success = False
                    self.err_msg = "Exception: WebGridPageView(): get_queryset(): Unrecognized option for self.req_sort_dir: {}".format(self.req_sort_dir)
                    print(self.err_msg)
                    return IndicatorData.objects.none()
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: WebGridPageView(): get_queryset(): Sorting by {}, {}: {}".format(self.req_sort_by, self.req_sort_dir, e)
            print(self.err_msg)
            return IndicatorData.objects.none()

        ## Get dropdown list values (Don't move this function, needs to be after the filtered and sorted dataset, to pull unique title, years and months base on current context)
        try:
            self.uniq_titles = indicator_data_entries.order_by('indicator__indicator_title').values('indicator__indicator_title').distinct()

            self.uniq_years = indicator_data_entries.order_by('year_month__yyyy').values('year_month__yyyy').distinct()

            self.uniq_months = indicator_data_entries.order_by('year_month__mm').values('year_month__mm').distinct()

            self.uniq_fiscal_years = indicator_data_entries.order_by('year_month__fiscal_year').values('year_month__fiscal_year').distinct()

            if self.client_is_admin == True:
                self.uniq_categories = indicator_data_entries.order_by('indicator__category__category_name').values('indicator__category__category_name').distinct()
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: WebGridPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return IndicatorData.objects.none()

        self.req_success = True
        return indicator_data_entries

    def get_context_data(self, **kwargs):
        try:
            ## Call the base implementation first to get a context
            context = super().get_context_data(**kwargs)

            ## Construct current context filter and sort GET param string, for front end to keep states
            ctx_title_filter_param = ""
            ctx_yyyy_filter_param = ""
            ctx_mm_filter_param = ""
            ctx_fiscal_year_filter_param = ""
            ctx_cat_filter_param = ""

            ## Construct Filter GET Param
            for each in self.req_title_list_filter:
                ctx_title_filter_param = "{}TitleListFilter={}&".format(ctx_title_filter_param, each)
            ### At this point, your ctx_title_filter_param  is something like "TitleListFilter=Facebook&TitleListFilter=Instagram&"
            for each in self.req_yr_list_filter:
                ctx_yyyy_filter_param = "{}YYYYListFilter={}&".format(ctx_yyyy_filter_param, each)
            for each in self.req_mn_list_filter:
                ctx_mm_filter_param = "{}MMListFilter={}&".format(ctx_mm_filter_param, each)
            for each in self.req_fy_list_filter:
                ctx_fiscal_year_filter_param = "{}FiscalYearListFilter={}&".format(ctx_fiscal_year_filter_param, each)
            if self.client_is_admin == True:
                for each in self.req_cat_list_filter:
                    ctx_cat_filter_param = "{}CategoriesListFilter={}&".format(ctx_cat_filter_param, each)

            ## Construct <a></a> GET parameter for the sorting columns
            ### Defaults
            ctx_title_sort_dir = "SortDir=asc&"
            ctx_yyyy_sort_dir = "SortDir=asc&"
            ctx_mm_sort_dir = "SortDir=asc&"
            ctx_fiscal_year_sort_dir = "SortDir=asc&"
            ctx_cat_sort_dir = "SortDir=asc&"
            ### Getting off of defaults on a need to basis
            if self.req_sort_by == 'indicator__indicator_title':
                if self.req_sort_dir == 'asc':
                    ctx_title_sort_dir = "SortDir=desc&"
            elif self.req_sort_by == 'year_month__yyyy':
                if self.req_sort_dir == 'asc':
                    ctx_yyyy_sort_dir = "SortDir=desc&"
            elif self.req_sort_by == 'year_month__mm':
                if self.req_sort_dir == 'asc':
                    ctx_mm_sort_dir = "SortDir=desc&"
            elif self.req_sort_by == 'year_month__fiscal_year':
                if self.req_sort_dir == 'asc':
                    ctx_fiscal_year_sort_dir = "SortDir=desc&"
            elif self.req_sort_by == 'indicator__category__category_name':
                if self.req_sort_dir == 'asc':
                    ctx_cat_sort_dir = "SortDir=desc&"


            self.title_sort_anchor_GET_param = "SortBy=indicator__indicator_title&{}{}{}{}{}{}".format(ctx_title_sort_dir, ctx_title_filter_param, ctx_yyyy_filter_param, ctx_mm_filter_param, ctx_fiscal_year_filter_param, ctx_cat_filter_param)
            self.yyyy_sort_anchor_GET_param = "SortBy=year_month__yyyy&{}{}{}{}{}{}".format(ctx_yyyy_sort_dir, ctx_title_filter_param, ctx_yyyy_filter_param, ctx_mm_filter_param, ctx_fiscal_year_filter_param, ctx_cat_filter_param)
            self.mm_sort_anchor_GET_param = "SortBy=year_month__mm&{}{}{}{}{}{}".format(ctx_mm_sort_dir, ctx_title_filter_param, ctx_yyyy_filter_param, ctx_mm_filter_param, ctx_fiscal_year_filter_param, ctx_cat_filter_param)
            self.fiscal_year_sort_anchor_GET_param = "SortBy=year_month__fiscal_year&{}{}{}{}{}{}".format(ctx_fiscal_year_sort_dir, ctx_title_filter_param, ctx_yyyy_filter_param, ctx_mm_filter_param, ctx_fiscal_year_filter_param, ctx_cat_filter_param)
            self.cat_sort_anchor_GET_param = "SortBy=indicator__category__category_name&{}{}{}{}{}{}".format(ctx_cat_sort_dir, ctx_title_filter_param, ctx_yyyy_filter_param, ctx_mm_filter_param, ctx_fiscal_year_filter_param, ctx_cat_filter_param)
            ### At this point, your self.title_sort_anchor_GET_param is something like
            ### "SortBy=indicator__indicator_title&SortDir=desc&title_list=Facebook&title_list=Instagram&yr_list=2019&yr_list=2020&mn_list=2&mn_list=1"

            ## Construct the context filter and sort param (This is your master param, as it contains all the Sort By and Filter By information, except Paging By information. The paging part of the param is handled in the front end PerInd.template.webgrid.html)
            self.ctx_pagination_param = "SortBy={}&SortDir={}&{}{}{}{}{}".format(self.req_sort_by, self.req_sort_dir, ctx_title_filter_param, ctx_yyyy_filter_param, ctx_mm_filter_param, ctx_fiscal_year_filter_param, ctx_cat_filter_param)


            ## Finally, setting the context variables
            ## Add my own variables to the context for the front end to shows
            context["req_success"] = self.req_success
            context["category_permissions"] = self.category_permissions
            context["err_msg"] = self.err_msg

            context["sort_dir"] = self.req_sort_dir
            context["sort_by"] = self.req_sort_by

            context["uniq_titles"] = self.uniq_titles
            context["uniq_years"] = self.uniq_years
            context["uniq_fiscal_years"] = self.uniq_fiscal_years
            context["uniq_months"] = self.uniq_months
            context["uniq_categories"] = self.uniq_categories

            context["ctx_title_list_filter"] = self.req_title_list_filter
            context["ctx_yr_list_filter"] = self.req_yr_list_filter
            context["ctx_mn_list_filter"] = self.req_mn_list_filter
            context["ctx_fy_list_filter"] = self.req_fy_list_filter
            context["ctx_cat_list_filter"] = self.req_cat_list_filter

            context["title_sort_anchor_GET_param"] = self.title_sort_anchor_GET_param
            context["yyyy_sort_anchor_GET_param"] = self.yyyy_sort_anchor_GET_param
            context["mm_sort_anchor_GET_param"] = self.mm_sort_anchor_GET_param
            context["fiscal_year_sort_anchor_GET_param"] = self.fiscal_year_sort_anchor_GET_param
            context["cat_sort_anchor_GET_param"] = self.cat_sort_anchor_GET_param

            context["ctx_pagination_param"] = self.ctx_pagination_param

            context["client_is_admin"] = self.client_is_admin

            return context
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: get_context_data(): {}".format(e)
            print(self.err_msg)

            context = super().get_context_data(**kwargs)
            context["req_success"] = self.req_success
            context["err_msg"] = self.err_msg

            context["indicator_data_entries"] = IndicatorData.objects.none()

            context["category_permissions"] = ""

            context["sort_dir"] = ""
            context["sort_by"] = ""

            context["uniq_titles"] = []
            context["uniq_years"] = []
            context["uniq_fiscal_years"] = []
            context["uniq_months"] = []
            context["uniq_categories"] = []

            context["ctx_title_list_filter"] = ""
            context["ctx_yr_list_filter"] = ""
            context["ctx_mn_list_filter"] = ""
            context["ctx_fy_list_filter"] = ""
            context["ctx_cat_list_filter"] = ""

            context["title_sort_anchor_GET_param"] = ""
            context["yyyy_sort_anchor_GET_param"] = ""
            context["mm_sort_anchor_GET_param"] = ""
            context["fiscal_year_sort_anchor_GET_param"] = ""
            context["cat_sort_anchor_GET_param"] = ""

            context["ctx_pagination_param"] = ""

            context["client_is_admin"] = False
            return context

## Post request
def SavePerIndDataApi(request):
    id = request.POST.get('id', '')
    table = request.POST.get('table', '')
    column = request.POST.get('column', '')
    new_value = request.POST.get('new_value', '')

    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: SavePerIndDataApi(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "SavePerIndDataApi():\n\nUNAUTHENTICATE USER!",
        })

    ## Make sure User is an Active User
    is_active_user = user_is_active_user(request.user)
    if is_active_user["success"] != True:
        print("Warning: SavePerIndDataApi(): USER '{}' is not an active user!".format(remote_user))
        return JsonResponse({
            "post_success": False,
            "post_msg": "Warning: SavePerIndDataApi(): USER '{}' is not an active user!".format(remote_user),
        })

    ## Authenticate permission for user
    user_perm_chk = user_has_permission_to_edit(remote_user, id)
    if user_perm_chk["success"] == False:
        print("Warning: SavePerIndDataApi(): USER '{}' has no permission to edit record #{}!".format(remote_user, id))
        return JsonResponse({
            "post_success": False,
            "post_msg": "SavePerIndDataApi():\n\nUSER '{}' has no permission to edit record #{}: SavePerIndDataApi(): {}".format(remote_user, id, user_perm_chk["err"]),
        })


    ## Make sure new_value is convertable to float
    try:
        new_value = float(new_value)
    except Exception as e:
        print("Error: SavePerIndDataApi(): Unable to convert new_value '{}' to float type, did not save the value".format(new_value))
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: SavePerIndDataApi():\n\nUnable to convert new_value '{}' to float type, did not save the value".format(new_value),
        })

    if table == "IndicatorData":
        row = IndicatorData.objects.get(record_id=id)

        if column=="val":
            try:
                row.val = new_value

                ## Update [last updated by] to current remote user, also make sure it's active user
                user_obj = Users.objects.get(login=remote_user, active_user=True) ## Will throw exception if no user is found with the criteria: "Users matching query does not exist.""
                row.update_user = user_obj

                ## Update [updated date] to current time
                ## updated_timestamp = datetime.now() ## Give 'naive' local time, which happens to be EDT on my home dev machine
                updated_timestamp = timezone.now() ## Give 'time zone awared' datetime, but backend is UTC
                row.updated_date = updated_timestamp

                local_updated_timestamp_str_response = updated_timestamp.astimezone(pytz.timezone('America/New_York')).strftime("%B %d, %Y, %I:%M %p")

                row.save()

                print("Api Log: SavePerIndDataApi(): User '{}' has successfully update '{}' to [{}].[{}] for record id '{}'".format(remote_user, new_value, table, column, id))
                return JsonResponse({
                    "post_success": True,
                    "post_msg": "",
                    "value_saved": "",
                    "updated_timestamp": local_updated_timestamp_str_response,
                    "updated_by": remote_user,
                })
            except Exception as e:
                print("Error: SavePerIndDataApi(): While trying to save to the database: {}".format(e))
                return JsonResponse({
                    "post_success": False,
                    "post_msg": "Error: SavePerIndDataApi():\n\nWhile trying to save to the database: {}".format(e),
                })

    print("Warning: SavePerIndDataApi(): Did not know what to do with the request. The request:\n\nid: '{}'\n table: '{}'\n column: '{}'\n new_value: '{}'\n".format(id, table, column, new_value))
    return JsonResponse({
        "post_success": False,
        "post_msg": "Warning: SavePerIndDataApi():\n\nDid not know what to do with the request. The request:\n\nid: '{}'\n table: '{}'\n column: '{}'\n new_value: '{}'\n".format(id, table, column, new_value),
    })

## Post request
def GetCsvApi(request):
    from django.db import connection
    """
    Download WebGrid view with all current context as xlsx.
    Expects all the filter and sort context in the request. (Don't need pagination context)
    """
    import csv
    from io import StringIO

    dummy_in_mem_file = StringIO()
    csv_queryset = None
    client_is_admin = False

    ## Collect GET url parameter info
    req_sort_dir = ""
    req_sort_by = ""

    temp_sort_dir = request.POST.get('SortDir')
    if (temp_sort_dir is not None and temp_sort_dir != '') and (temp_sort_dir == 'asc' or temp_sort_dir == 'desc'):
        req_sort_dir = temp_sort_dir

    temp_sort_by = request.POST.get('SortBy')
    if (temp_sort_by is not None and temp_sort_by != ''):
        req_sort_by = temp_sort_by

    req_title_list_filter = request.POST.getlist('TitleListFilter[]')
    req_yr_list_filter = request.POST.getlist('YYYYListFilter[]')
    req_mn_list_filter = request.POST.getlist('MMListFilter[]')
    req_fy_list_filter = request.POST.getlist('FiscalYearListFilter[]')
    req_cat_list_filter = request.POST.getlist('CategoriesListFilter[]')

    ## print("req_sort_dir: {}".format(req_sort_dir))
    ## print("req_sort_by: {}".format(req_sort_by))
    ## print("req_title_list_filter: {}".format(req_title_list_filter))
    ## print("req_yr_list_filter: {}".format(req_yr_list_filter))
    ## print("req_mn_list_filter: {}".format(req_mn_list_filter))
    ## print("req_fy_list_filter: {}".format(req_fy_list_filter))
    ## print("req_cat_list_filter: {}".format(req_cat_list_filter))

    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: SavePerIndDataApi(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "SavePerIndDataApi():\n\nUNAUTHENTICATE USER!",
            "post_data": None,
        })

    ## Get list authorized Categories of Indicator Data, and log the category_permissions
    is_active_admin = user_is_active_admin(request.user)
    if is_active_admin["success"] == True:
        client_is_admin = True
        user_cat_permissions = get_admin_category_permissions()
    elif is_active_admin["success"] == False:
        client_is_admin = False

        is_active_user = user_is_active_user(request.user)
        if is_active_user["success"] == True:
            ## If not admin, do standard filter with categories
            user_cat_permissions = get_user_category_permissions(request.user)
        else:
            print("GetCsvApi(): {}".format(is_active_user["err"]))
            return JsonResponse({
                "post_success": False,
                "post_msg": "GetCsvApi(): {}".format(is_active_user["err"]),
                "post_data": None,
            })

    elif is_active_admin["success"] is None:
        return JsonResponse({
            "post_success": False,
            "post_msg": "GetCsvApi(): {}".format(is_active_admin["err"]),
            "post_data": None,
        })

    ## Get list authorized Categories of Indicator Data, and log the category_permissions
    if user_cat_permissions["success"] == True:
        category_pk_list = user_cat_permissions["pk_list"]
    elif (user_cat_permissions["success"] == False) or (user_cat_permissions["success"] is None):
        return JsonResponse({
            "post_success": False,
            "post_msg": "GetCsvApi(): {}".format(user_cat_permissions['err']),
            "post_data": None,
        })
    else:
        return JsonResponse({
            "post_success": False,
            "post_msg": "GetCsvApi(): user_cat_permissions['success'] has an unrecognized value: {}".format(user_cat_permissions['success']),
            "post_data": None,
        })

    ## Default filters on the WebGrid dataset
    try:
        csv_queryset = IndicatorData.objects.filter(
            indicator__category__pk__in=category_pk_list, ## Filters for authorized Categories
            indicator__active=True, ## Filters for active Indicator titles
            year_month__yyyy__gt=timezone.now().year-4, ## Filter for only last four year, "yyyy_gt" is "yyyy greater than"
        )

        csv_queryset = csv_queryset.exclude(  ## Exclude any future dates greater than current month and current year
            Q(
                year_month__yyyy__exact=timezone.now().year,
                year_month__mm__gt=timezone.now().month
            ) |
            Q(
                year_month__yyyy__gt=timezone.now().year,
            )
        )
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "GetCsvApi(): Failed to get any data from queryset: {}\n\nErr Msg: {}".format(user_perm_chk["err"], e),
            "post_data": None,
        })

    ## Query for the queryset with matching filter and sort criteria
    ## Filter by Titles
    if len(req_title_list_filter) >= 1:
        try:
            qs = Q()
            for i in req_title_list_filter:
                qs = qs | Q(indicator__indicator_title=i)
            csv_queryset = csv_queryset.filter(qs)
        except Exception as e:
            return JsonResponse({
                "post_success": False,
                "post_msg": "GetCsvApi(): Failed to filter Titles from queryset\n\nErr Msg: {}".format(e),
                "post_data": None,
            })
    ## Filter by YYYYs
    if len(req_yr_list_filter) >= 1:
        try:
            qs = Q()
            for i in req_yr_list_filter:
                qs = qs | Q(year_month__yyyy=i)
            csv_queryset = csv_queryset.filter(qs)
        except Exception as e:
            return JsonResponse({
                "post_success": False,
                "post_msg": "GetCsvApi(): Failed to filter YYYY from queryset\n\nErr Msg: {}".format(e),
                "post_data": None,
            })
    ## Filter by MMs
    if len(req_mn_list_filter) >= 1:
        try:
            qs = Q()
            for i in req_mn_list_filter:
                qs = qs | Q(year_month__mm=i)
            csv_queryset = csv_queryset.filter(qs)
        except Exception as e:
            return JsonResponse({
                "post_success": False,
                "post_msg": "GetCsvApi(): Failed to filter MM from queryset\n\nErr Msg: {}".format(e),
                "post_data": None,
            })
    ## Filter by Fiscal Years
    if len(req_fy_list_filter) >= 1:
        try:
            qs = Q()
            for i in req_fy_list_filter:
                qs = qs | Q(year_month__fiscal_year=i)
            csv_queryset = csv_queryset.filter(qs)
        except Exception as e:
            return JsonResponse({
                "post_success": False,
                "post_msg": "GetCsvApi(): Failed to filter FY from queryset\n\nErr Msg: {}".format(e),
                "post_data": None,
            })
    ## Filter by Categories
    if client_is_admin == True:
        if len(req_cat_list_filter) >= 1:
            try:
                qs = Q()
                for i in req_cat_list_filter:
                    qs = qs | Q(indicator__category__category_name=i)
                csv_queryset = csv_queryset.filter(qs)
            except Exception as e:
                return JsonResponse({
                    "post_success": False,
                    "post_msg": "GetCsvApi(): Failed to filter Categories from queryset\n\nErr Msg: {}".format(e),
                    "post_data": None,
                })

    ## Sort dataset from sort direction and sort column
    try:
        ## Default sort
        if req_sort_by == '':
            csv_queryset = csv_queryset.order_by('indicator__category__category_name', '-year_month__fiscal_year', '-year_month__mm', 'indicator__indicator_title')
        else:
            if req_sort_dir == "asc":
                csv_queryset = csv_queryset.order_by(req_sort_by)
            elif req_sort_dir == "desc":
                csv_queryset = csv_queryset.order_by('-{}'.format(req_sort_by))
            else:
                return JsonResponse({
                    "post_success": False,
                    "post_msg": "GetCsvApi(): Failed to sort, unrecognize req_sort_dir: {}".format(req_sort_dir),
                    "post_data": None,
                })
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "GetCsvApi(): Failed to sort from queryset\n\nErr Msg: {}".format(e),
            "post_data": None,
        })

    ## Convert to CSV
    writer = csv.writer(dummy_in_mem_file)
    writer.writerow(['Category', 'Indicator Title', 'Fiscal Year', 'Month', 'Indicator Value', 'Units', 'Multiplier', 'Updated Date', 'Last Updated By', ])
    ## More on select_related: https://docs.djangoproject.com/en/3.1/ref/models/querysets/ and https://medium.com/@hansonkd/performance-problems-in-the-django-orm-1f62b3d04785
    for each in csv_queryset.select_related():
        if each.year_month.mm == 1:
            month_name = 'Jan'
        elif each.year_month.mm == 2:
            month_name = 'Feb'
        elif each.year_month.mm == 3:
            month_name = 'Mar'
        elif each.year_month.mm == 4:
            month_name = 'Apr'
        elif each.year_month.mm == 5:
            month_name = 'May'
        elif each.year_month.mm == 6:
            month_name = 'Jun'
        elif each.year_month.mm == 7:
            month_name = 'Jul'
        elif each.year_month.mm == 8:
            month_name = 'Aug'
        elif each.year_month.mm == 9:
            month_name = 'Sep'
        elif each.year_month.mm == 10:
            month_name = 'Oct'
        elif each.year_month.mm == 11:
            month_name = 'Nov'
        elif each.year_month.mm == 12:
            month_name = 'Dec'
        else:
            month_name = 'Unknown Month'

        eachrow = [
            each.indicator.category.category_name,
            each.indicator,
            each.year_month.fiscal_year,
            month_name,
            each.val,
            each.indicator.unit.unit_type,
            each.indicator.val_multiplier.multiplier_scale,
            each.updated_date.strftime("%m/%d/%Y"),
            each.update_user,
        ]
        writer.writerow(eachrow)

    return JsonResponse({
        "post_success": True,
        "post_msg": "GetCsvApi(): Success, check for variable 'post_data' in the response JSON for the csv file",
        "post_data": dummy_in_mem_file.getvalue(),
    })

## For admin access only
class PastDueIndicatorsPageView(generic.ListView):
    template_name = 'PerInd.template.pastdueindicators.html'
    context_object_name = 'indicator_data_entries'

    paginate_by = 24

    req_success = False
    err_msg = ""

    req_sort_dir = ""
    req_sort_by = ""

    uniq_categories = []

    req_cat_list_filter = [] ## Category

    ctx_pagination_param = ""

    cat_sort_anchor_GET_param = ""

    client_is_admin = False

    def get_queryset(self):
        ## Collect GET url parameter info
        temp_sort_dir = self.request.GET.get('SortDir')
        if (temp_sort_dir is not None and temp_sort_dir != '') and (temp_sort_dir == 'asc' or temp_sort_dir == 'desc'):
            self.req_sort_dir = temp_sort_dir

        temp_sort_by = self.request.GET.get('SortBy')
        if (temp_sort_by is not None and temp_sort_by != ''):
            self.req_sort_by = temp_sort_by

        self.req_cat_list_filter = self.request.GET.getlist('CategoriesListFilter')

        ## Check for Active Admins
        is_active_admin = user_is_active_admin(self.request.user)
        if is_active_admin["success"] == True:
            self.client_is_admin = True
        else:
            self.req_success = False
            self.err_msg = "Exception: PastDueIndicatorsPageView(): get_queryset(): {} is not an Admin and is not authorized to see this page".format(self.request.user)
            print(self.err_msg)
            return IndicatorData.objects.none()

        ## Use python to process the queryset to find a list of Indicator_Data.Records_IDs that meet the Past-Due-Criteria
        ## Criteria for past due, last month entered is at least two months in the past (Updated_Date = '1899-12-30', means no data was entered, it is also our default 'NULL/Empty' date)
        try:
            base_data_qs = IndicatorData.objects.filter(
                indicator__active=True, ## Filters for active Indicator titles
                year_month__yyyy__gt=timezone.now().year-4, ## Filter for only last four year, "yyyy_gt" is "yyyy greater than"
            )

            base_data_qs = base_data_qs.exclude(  ## Exclude any future dates greater than current month and current year
                Q(
                    year_month__yyyy__exact=timezone.now().year,
                    year_month__mm__gt=timezone.now().month
                ) |
                Q(
                    year_month__yyyy__gt=timezone.now().year,
                )
            )

            ## Find out out past due entry here
            past_due_record_id_list = []
            unique_ind_id = base_data_qs.order_by('indicator_id').values('indicator_id').distinct()
            for each_ind_id in unique_ind_id:
                ind_id_related = base_data_qs.filter(indicator_id__exact=each_ind_id['indicator_id']).order_by('indicator_id', '-year_month__yyyy', '-year_month__mm')

                for each_row in ind_id_related:
                    ## Indicator could be up-to-date, current record is for entry for the last two month (Counting current month and last month)
                    if each_row.year_month.yyyy == timezone.now().year and ( timezone.now().month - each_row.year_month.mm ) < 2:
                        if each_row.updated_date.date().year != datetime(1899, 12, 30).date().year:
                            # Indicator is up-to-date, abort loop and go scan the next Indicator
                            break
                        else:
                            # check the next record
                            continue
                    ## Indicator is pass-dued (current record is for entry over two months ago, before current month and last month), find the latest record where data was entered.
                    else:
                        if each_row.updated_date.date().year != datetime(1899, 12, 30).date().year:
                            ## Found latest record where data was entered, break loop and scan the next Indicator
                            past_due_record_id_list.append(each_row.record_id)
                            break
                        else:
                            # check the next record
                            continue

            ## Use the following query to verify what is shown on the website is actaully outdated records by more than 2 month and shows just the latest record that was entered for each indicator title
            """
            SELECT
            Indicator_Data.Record_ID,
            Indicator_Data.Indicator_ID,
            Year_Month.YYYY,
            Year_Month.MM,
            Indicator_Data.Updated_Date,
            Users.Login
            ,Indicator_Title
            --ROW_NUMBER() OVER (PARTITION BY Indicator_Data.Indicator_ID ORDER BY Indicator_Data.Indicator_ID, Fiscal_Year DESC, MM DESC) AS rank
            FROM Indicator_Data
            LEFT JOIN Indicator_List
            ON Indicator_Data.Indicator_ID = Indicator_List.Indicator_ID
            LEFT JOIN Year_Month
            ON Indicator_Data.Year_Month_ID = Year_Month.Year_Month_ID
            LEFT JOIN Users
            ON Indicator_Data.Update_User_ID = Users.User_ID
            LEFT JOIN Category
            ON Indicator_List.Category_ID = Category.Category_ID
            WHERE
            Indicator_Title = 'ENTER YOU INDICATOR TITLE HERE' AND
            Indicator_List.Active = 1 AND
            --Indicator_Data.Updated_Date = '1899-12-30 00:00:00' AND
            --Users.Login = 'Unknown' AND
            Year_Month.YYYY > YEAR(GETDATE()) - 4 AND
            NOT( Year_Month.YYYY = YEAR(GETDATE()) AND Year_Month.MM > MONTH(GETDATE()) )
            ORDER BY
            Indicator_ID,
            YYYY DESC,
            MM DESC
            """
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: PastDueIndicatorsPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return IndicatorData.objects.none()

        ## Requery db to match up with the list of Indicator_Data.Records_IDs to pass to the client
        try:
            indicator_data_entries = IndicatorData.objects.filter(
                pk__in=past_due_record_id_list,
            )
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: PastDueIndicatorsPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return IndicatorData.objects.none()

        ## refrencee: https://stackoverflow.com/questions/5956391/django-objects-filter-with-list
        ## Filter dataset from Dropdown list
        ## Filter by Categories
        if len(self.req_cat_list_filter) >= 1:
            try:
                qs = Q()
                for i in self.req_cat_list_filter:
                    qs = qs | Q(indicator__category__category_name=i)
                indicator_data_entries = indicator_data_entries.filter(qs)
            except Exception as e:
                self.req_success = False
                self.err_msg = "Exception: PastDueIndicatorsPageView(): get_queryset(): Categories Filtering: {}".format(e)
                print(self.err_msg)
                return IndicatorData.objects.none()

        ## Sort dataset from sort direction and sort column
        try:
            ## Default sort
            if self.req_sort_by == '':
                #@TODO
                indicator_data_entries = indicator_data_entries.order_by('indicator__category__category_name', '-year_month__fiscal_year', '-year_month__mm', 'indicator__indicator_title')
            else:
                if self.req_sort_dir == "asc":
                    indicator_data_entries = indicator_data_entries.order_by(self.req_sort_by)
                elif self.req_sort_dir == "desc":
                    indicator_data_entries = indicator_data_entries.order_by('-{}'.format(self.req_sort_by))
                else:
                    self.req_success = False
                    self.err_msg = "Exception: PastDueIndicatorsPageView(): get_queryset(): Unrecognized option for self.req_sort_dir: {}".format(self.req_sort_dir)
                    print(self.err_msg)
                    return IndicatorData.objects.none()
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: PastDueIndicatorsPageView(): get_queryset(): Sorting by {}, {}: {}".format(self.req_sort_by, self.req_sort_dir, e)
            print(self.err_msg)
            return IndicatorData.objects.none()

        ## Get dropdown list values (Don't move this function, needs to be after the filtered and sorted dataset, to pull unique title, years and months base on current context)
        try:
            self.uniq_categories = indicator_data_entries.order_by('indicator__category__category_name').values('indicator__category__category_name').distinct()
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: PastDueIndicatorsPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return IndicatorData.objects.none()

        self.req_success = True
        return indicator_data_entries

    def get_context_data(self, **kwargs):
        try:
            ## Call the base implementation first to get a context
            context = super().get_context_data(**kwargs)

            ## Construct current context filter and sort GET param string, for front end to keep states
            ctx_cat_filter_param = ""

            ## Construct Filter GET Param
            for each in self.req_cat_list_filter:
                ctx_cat_filter_param = "{}CategoriesListFilter={}&".format(ctx_cat_filter_param, each)
                ### At this point, your ctx_cat_filter_param  is something like "CategoriesListFilter=1&CategoriesListFilter=2&"

            ## Construct <a></a> GET parameter for the sorting columns
            ### Defaults
            ctx_cat_sort_dir = "SortDir=asc&"
            ### Getting off of defaults on a need to basis
            if self.req_sort_by == 'indicator__category__category_name':
                if self.req_sort_dir == 'asc':
                    ctx_cat_sort_dir = "SortDir=desc&"

            self.cat_sort_anchor_GET_param = "SortBy=indicator__category__category_name&{}{}".format(ctx_cat_sort_dir, ctx_cat_filter_param)

            ## Construct the context filter and sort param (This is your master param, as it contains all the Sort By and Filter By information, except Paging By information. The paging part of the param is handled in the front end PerInd.template.webgrid.html)
            self.ctx_pagination_param = "SortBy={}&SortDir={}&{}".format(self.req_sort_by, self.req_sort_dir, ctx_cat_filter_param)


            ## Finally, setting the context variables
            ## Add my own variables to the context for the front end to shows
            context["req_success"] = self.req_success
            context["err_msg"] = self.err_msg

            context["sort_dir"] = self.req_sort_dir
            context["sort_by"] = self.req_sort_by

            context["uniq_categories"] = self.uniq_categories

            context["ctx_cat_list_filter"] = self.req_cat_list_filter

            context["cat_sort_anchor_GET_param"] = self.cat_sort_anchor_GET_param

            context["ctx_pagination_param"] = self.ctx_pagination_param

            context["client_is_admin"] = self.client_is_admin

            return context
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: get_context_data(): {}".format(e)
            print(self.err_msg)

            context = super().get_context_data(**kwargs)
            context["req_success"] = self.req_success
            context["err_msg"] = self.err_msg

            context["indicator_data_entries"] = IndicatorData.objects.none()

            context["sort_dir"] = ""
            context["sort_by"] = ""

            context["uniq_categories"] = []

            context["ctx_cat_list_filter"] = ""

            context["cat_sort_anchor_GET_param"] = ""

            context["ctx_pagination_param"] = ""

            context["client_is_admin"] = False
            return context

class AdminPanelPageView(generic.ListView):
    template_name = 'PerInd.template.adminpanel.html'

    req_success = False
    err_msg = ""

    client_is_admin = False

    def get_queryset(self):
        ## Check for Active User
        is_active_user = user_is_active_user(self.request.user)
        if is_active_user["success"] == True:
            pass
        else:
            self.req_success = False
            self.err_msg = "AdminPanelPageView(): get_queryset(): {}".format(is_active_user["err"])
            print(self.err_msg)
            return

        ## Check for Active Admins
        is_active_admin = user_is_active_admin(self.request.user)
        if is_active_admin["success"] == True:
            self.client_is_admin = True
        else:
            self.req_success = False
            self.err_msg = "AdminPanelPageView(): get_queryset(): {} is not an Admin and is not authorized to see this page".format(self.request.user)
            print(self.err_msg)
            return

        self.req_success = True

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

class UserPermissionsPanelPageView(generic.ListView):
    template_name = 'PerInd.template.userpermissionspanel.html'
    context_object_name = 'permission_data_entries'

    req_success = False
    err_msg = ""

    client_is_admin = False

    users_list = []
    categories_list = []
    def get_queryset(self):
        ## Check for Active User
        is_active_user = user_is_active_user(self.request.user)
        if is_active_user["success"] == True:
            pass
        else:
            self.req_success = False
            self.err_msg = "UserPermissionsPanelPageView(): get_queryset(): {}".format(is_active_user["err"])
            print(self.err_msg)
            return UserPermissions.objects.none()

        ## Check for Active Admins
        is_active_admin = user_is_active_admin(self.request.user)
        if is_active_admin["success"] == True:
            self.client_is_admin = True
        else:
            self.req_success = False
            self.err_msg = "UserPermissionsPanelPageView(): get_queryset(): {} is not an Admin and is not authorized to see this page".format(self.request.user)
            print(self.err_msg)
            return UserPermissions.objects.none()

        ## Get the permissions data
        try:
            permission_data_entries = UserPermissions.objects.all().order_by('user__login')
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: UserPermissionsPanelPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return UserPermissions.objects.none()

        # ## EXAMPLE: Get the active users login list in json format
        # try:
        #     user_objs = Users.objects.filter(
        #         active_user=True
        #     ).order_by('login')

        #     py_list_obj = [x.login for x in user_objs]
        #     json_obj = json.dumps(py_list_obj)
        #     self.user_logins_json = json_obj
        # except Exception as e:
        #     self.req_success = False
        #     self.err_msg = "Exception: UserPermissionsPanelPageView(): get_queryset(): {}".format(e)
        #     print(self.err_msg)
        #     return UserPermissions.objects.none()


        ## Get the active users login list
        try:
            user_objs = Users.objects.filter(
                active_user=True
            ).order_by('login')

            self.users_list = user_objs
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: UserPermissionsPanelPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return UserPermissions.objects.none()

        ## Get the category list
        try:
            category_objs = Category.objects.all().order_by('category_name')
            self.categories_list = category_objs
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: UserPermissionsPanelPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return UserPermissions.objects.none()

        self.req_success = True
        return permission_data_entries

    def get_context_data(self, **kwargs):
        try:
            ## Call the base implementation first to get a context
            context = super().get_context_data(**kwargs)

            ## Finally, setting the context variables
            ## Add my own variables to the context for the front end to shows
            context["req_success"] = self.req_success
            context["err_msg"] = self.err_msg

            context["client_is_admin"] = self.client_is_admin

            context["users_list"] = self.users_list
            context["categories_list"] = self.categories_list
            return context
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: get_context_data(): {}".format(e)
            print(self.err_msg)

            context = super().get_context_data(**kwargs)
            context["req_success"] = self.req_success
            context["err_msg"] = self.err_msg

            context["client_is_admin"] = False

            context["users_list"] = []
            context["categories_list"] = []
            return context

## Post request - for single cell edits
def UserPermissionsPanelApiUpdateData(request):
    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UserPermissionsPanelApiUpdateData():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    id = json_blob['id']
    table = json_blob['table']
    column = json_blob['column']
    new_value = json_blob['new_value']

    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: UserPermissionsPanelApiUpdateData(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "UserPermissionsPanelApiUpdateData():\n\nUNAUTHENTICATE USER!",
            "post_data": None,
        })

    ## Check active user
    is_active_user = user_is_active_user(request.user)
    if is_active_user["success"] == True:
        pass
    else:
        print("UserPermissionsPanelApiUpdateData(): {}".format(is_active_user["err"]))
        return JsonResponse({
            "post_success": False,
            "post_msg": "UserPermissionsPanelApiUpdateData(): {}".format(is_active_user["err"]),
            "post_data": None,
        })

    ## Check active admin
    is_active_admin = user_is_active_admin(request.user)
    if is_active_admin["success"] == True:
        pass
    else:
        return JsonResponse({
            "post_success": False,
            "post_msg": "UserPermissionsPanelApiUpdateData(): {}".format(is_active_admin["err"]),
            "post_data": None,
        })

    ## Save the data
    if table == "Users":

        ## Make sure new_value is convertable to its respective data type
        if column == "Active_User":
            try:
                new_value = bool(new_value)
            except Exception as e:
                print("Error: UserPermissionsPanelApiUpdateData(): Unable to convert new_value '{}' to bool type, did not save the value".format(new_value))
                return JsonResponse({
                    "post_success": False,
                    "post_msg": "Error: UserPermissionsPanelApiUpdateData():\n\nUnable to convert new_value '{}' to bool type, did not save the value".format(new_value),
                })
        else:
            try:
                new_value = str(new_value)
            except Exception as e:
                print("Error: UserPermissionsPanelApiUpdateData(): Unable to convert new_value '{}' to str type, did not save the value".format(new_value))
                return JsonResponse({
                    "post_success": False,
                    "post_msg": "Error: UserPermissionsPanelApiUpdateData():\n\nUnable to convert new_value '{}' to str type, did not save the value".format(new_value),
                })

        ## Save the value
        try:
            row = UserPermissions.objects.get(user_permission_id=id)
            if column == "Login":
                try:
                    user_obj = Users.objects.get(login=new_value, active_user=True) ## Will throw exception if no user is found with the criteria: "Users matching query does not exist.""
                    row.user = user_obj

                    row.save()

                    # # Temp
                    # return JsonResponse({
                    #     "post_success": False,
                    #     "post_msg": "trying to save: '{}'".format(new_value),
                    # })

                    print("Api Log: UserPermissionsPanelApiUpdateData(): Client '{}' has successfully updated User_Permissions. For User_Permission_ID '{}' updated the User to '{}'".format(remote_user, id, new_value))
                    return JsonResponse({
                        "post_success": True,
                        "post_msg": "",
                    })
                except Exception as e:
                    print("Error: UserPermissionsPanelApiUpdateData(): While trying to update a User Permission record to login '{}': {}".format(new_value, e))
                    return JsonResponse({
                        "post_success": False,
                        "post_msg": "Error: UserPermissionsPanelApiUpdateData():\n\nWhile trying to a User Permission record to login '{}': {}".format(new_value, e),
                    })
        except Exception as e:
            print("Error: UserPermissionsPanelApiUpdateData(): While trying to update a User Permission record to login '{}': {}".format(new_value, e))
            return JsonResponse({
                "post_success": False,
                "post_msg": "Error: UserPermissionsPanelApiUpdateData():\n\nWhile trying to a User Permission record to login '{}': {}".format(new_value, e),
            })

    # elif table == "":
    #     pass


    print("Warning: UserPermissionsPanelApiUpdateData(): Did not know what to do with the request. The request:\n\nid: '{}'\n table: '{}'\n column: '{}'\n new_value: '{}'\n".format(id, table, column, new_value))
    return JsonResponse({
        "post_success": False,
        "post_msg": "Warning: UserPermissionsPanelApiUpdateData():\n\nDid not know what to do with the request. The request:\n\nid: '{}'\n table: '{}'\n column: '{}'\n new_value: '{}'\n".format(id, table, column, new_value),
    })

## For form add row
def UserPermissionsPanelApiAddRow(request):
    """
        Expects the post request to post a JSON object, and that it will contain login_selection and category_selection. Like so:
        {
            login_selection: "Some value",
            category_selection: "Some other value"
        }
        Will create a new row in the Permissions table with the selected login and category
    """

    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: UserPermissionsPanelApiAddRow(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "UserPermissionsPanelApiAddRow():\n\nUNAUTHENTICATE USER!",
        })

    ## Check active user
    is_active_user = user_is_active_user(request.user)
    if is_active_user["success"] == True:
        pass
    else:
        print("UserPermissionsPanelApiAddRow(): {}".format(is_active_user["err"]))
        return JsonResponse({
            "post_success": False,
            "post_msg": "UserPermissionsPanelApiAddRow(): {}".format(is_active_user["err"]),
        })

    ## Check active admin
    is_active_admin = user_is_active_admin(request.user)
    if is_active_admin["success"] == True:
        pass
    else:
        return JsonResponse({
            "post_success": False,
            "post_msg": "UserPermissionsPanelApiAddRow(): {}".format(is_active_admin["err"]),
        })

    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UserPermissionsPanelApiAddRow():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    ## Check login_selection and category_selection is not empty string
    try:
        login_selection = json_blob['login_selection']
        category_selection = json_blob['category_selection']

        if login_selection == "":
            return JsonResponse({
                "post_success": False,
                "post_msg": "login_selection cannot be an empty string".format(login_selection, category_selection),
            })

        if category_selection == "":
            return JsonResponse({
                "post_success": False,
                "post_msg": "category_selection cannot be an empty string".format(login_selection, category_selection),
            })
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UserPermissionsPanelApiAddRow():\n\nThe POSTed json obj does not have the following variable: {}".format(e),
        })

    ## Check that the login_selection and category_selection exists
    try:
        if not Users.objects.filter(login__exact=login_selection, active_user__exact=True).exists():
            return JsonResponse({
                "post_success": False,
                "post_msg": "'{}' doesn't exists or it's not an active user".format(login_selection),
            })
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UserPermissionsPanelApiAddRow(): {}".format(e),
        })

    try:
         if not Category.objects.filter(category_name__exact=category_selection).exists():
            return JsonResponse({
                "post_success": False,
                "post_msg": "'{}' doesn't exists as a Category".format(category_selection),
            })
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UserPermissionsPanelApiAddRow(): {}".format(e),
        })

    ## Check for duplication of login and category
    try:
        if UserPermissions.objects.filter(user__login__exact=login_selection, category__category_name__exact=category_selection).exists():
            return JsonResponse({
                "post_success": False,
                "post_msg": "'{}' already has access to '{}'".format(login_selection, category_selection),
            })
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UserPermissionsPanelApiAddRow(): {}".format(e),
        })

    ## Create the row!
    try:
        user_obj = Users.objects.get(login=login_selection, active_user=True)
        category_obj = Category.objects.get(category_name=category_selection)
        new_permission = UserPermissions(user=user_obj, category=category_obj)
        new_permission.save()
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UserPermissionsPanelApiAddRow(): {}".format(e),
        })

    return JsonResponse({
        "post_success": True,
        "post_msg": "",
        "permission_id": new_permission.user_permission_id,
        "first_name": user_obj.first_name,
        "last_name": user_obj.last_name,
        "active_user": user_obj.active_user,
        "login": user_obj.login,
        "category_name": category_obj.category_name,
    })

## For JS datatable delete row
def UserPermissionsPanelApiDeleteRow(request):
    """
        Expects the post request to post a JSON object, and that it will contain user_permission_id. Like so:
        {
            user_permission_id: "Some value"
        }
        Will delete row in the Permissions table with the given user_permission_id
    """

    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: UserPermissionsPanelApiDeleteRow(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "UserPermissionsPanelApiDeleteRow():\n\nUNAUTHENTICATE USER!",
        })

    ## Check active user
    is_active_user = user_is_active_user(request.user)
    if is_active_user["success"] == True:
        pass
    else:
        print("UserPermissionsPanelApiDeleteRow(): {}".format(is_active_user["err"]))
        return JsonResponse({
            "post_success": False,
            "post_msg": "UserPermissionsPanelApiDeleteRow(): {}".format(is_active_user["err"]),
        })

    ## Check active admin
    is_active_admin = user_is_active_admin(request.user)
    if is_active_admin["success"] == True:
        pass
    else:
        return JsonResponse({
            "post_success": False,
            "post_msg": "UserPermissionsPanelApiDeleteRow(): {}".format(is_active_admin["err"]),
        })

    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UserPermissionsPanelApiDeleteRow():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    ## Make sure user_permission_id is convertable to a unsign int
    try:
        user_permission_id = json_blob['user_permission_id']

        try:
            user_permission_id = int(user_permission_id)
        except Exception as e:
            return JsonResponse({
                "post_success": False,
                "post_msg": "user_permission_id cannot be converted to an int: '{}'".format(user_permission_id),
            })

        if user_permission_id <= 0:
            return JsonResponse({
                "post_success": False,
                "post_msg": "user_permission_id is less than or equal to zero: '{}'".format(user_permission_id),
            })
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UserPermissionsPanelApiDeleteRow():\n\nThe POSTed json obj does not have the following variable: {}".format(e),
        })

    ## Remove the permission row
    try:
        permission_row = UserPermissions.objects.get(user_permission_id=user_permission_id)
        permission_row.delete()
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UserPermissionsPanelApiDeleteRow():\n\nFailed to remove user_permission_id '{}' from database: '{}'".format(user_permission_id, e),
        })

    return JsonResponse({
        "post_success": True,
        "post_msg": "",
    })

class UsersPanelPageView(generic.ListView):
    template_name = 'PerInd.template.userspanel.html'
    context_object_name = 'users_data_entries'

    req_success = False
    err_msg = ""

    client_is_admin = False

    def get_queryset(self):
        ## Check for Active User
        is_active_user = user_is_active_user(self.request.user)
        if is_active_user["success"] == True:
            pass
        else:
            self.req_success = False
            self.err_msg = "UsersPanelPageView(): get_queryset(): {}".format(is_active_user["err"])
            print(self.err_msg)
            return Users.objects.none()

        ## Check for Active Admins
        is_active_admin = user_is_active_admin(self.request.user)
        if is_active_admin["success"] == True:
            self.client_is_admin = True
        else:
            self.req_success = False
            self.err_msg = "UsersPanelPageView(): get_queryset(): {} is not an Admin and is not authorized to see this page".format(self.request.user)
            print(self.err_msg)
            return Users.objects.none()

        ## Get the permissions data
        try:
            users_data_entries = Users.objects.all().order_by('login')
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: UsersPanelPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return Users.objects.none()

        self.req_success = True
        return users_data_entries

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

def UsersPanelApiAddRow(request):
    """
        Expects the post request to post a JSON object, and that it will contain first_name_input, last_name_input and login_input. Like so:
        {
            first_name_input: "Some value",
            last_name_input: "Some value",
            login_input: "Some value",
        }
        Will create a new row in the Users table with the given first name, last name and login. Default the active_user to True
    """

    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: UsersPanelApiAddRow(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "UsersPanelApiAddRow():\n\nUNAUTHENTICATE USER!",
        })

    ## Check active user
    is_active_user = user_is_active_user(request.user)
    if is_active_user["success"] == True:
        pass
    else:
        print("UsersPanelApiAddRow(): {}".format(is_active_user["err"]))
        return JsonResponse({
            "post_success": False,
            "post_msg": "UsersPanelApiAddRow(): {}".format(is_active_user["err"]),
        })

    ## Check active admin
    is_active_admin = user_is_active_admin(request.user)
    if is_active_admin["success"] == True:
        pass
    else:
        return JsonResponse({
            "post_success": False,
            "post_msg": "UsersPanelApiAddRow(): {}".format(is_active_admin["err"]),
        })

    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UsersPanelApiAddRow():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    ## Check json request param is not empty string
    try:
        first_name_input = json_blob['first_name_input']
        last_name_input = json_blob['last_name_input']
        login_input = json_blob['login_input']

        if first_name_input == "":
            return JsonResponse({
                "post_success": False,
                "post_msg": "first_name_input cannot be an empty string",
            })

        if last_name_input == "":
            return JsonResponse({
                "post_success": False,
                "post_msg": "last_name_input cannot be an empty string",
            })

        if login_input == "":
            return JsonResponse({
                "post_success": False,
                "post_msg": "login_input cannot be an empty string",
            })
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UsersPanelApiAddRow():\n\nThe POSTed json obj does not have the following variable: {}".format(e),
        })

    ## Check for duplication of login
    try:
        if Users.objects.filter(login__exact=login_input).exists():
            return JsonResponse({
                "post_success": False,
                "post_msg": "'{}' already exists in the Users table".format(login_input),
            })
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UsersPanelApiAddRow(): {}".format(e),
        })

    ## Create the row!
    try:
        new_user = Users(first_name=first_name_input, last_name=last_name_input, login=login_input, active_user=True)
        new_user.save()
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UsersPanelApiAddRow(): {}".format(e),
        })

    return JsonResponse({
        "post_success": True,
        "post_msg": "",
        "user_id": new_user.user_id,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name,
        "active_user": new_user.active_user,
        "login": new_user.login,
    })

def UsersPanelApiDeleteRow(request):
    """
        Expects the post request to post a JSON object, and that it will contain user_id. Like so:
        {
            user_id: "Some value"
        }
        Will delete row in the Users table with the given user_id.

        Delete will fail if there are any UserPermissions record associated with the Users.
    """

    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: UsersPanelApiDeleteRow(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "UsersPanelApiDeleteRow():\n\nUNAUTHENTICATE USER!",
        })

    ## Check active user
    is_active_user = user_is_active_user(request.user)
    if is_active_user["success"] == True:
        pass
    else:
        print("UsersPanelApiDeleteRow(): {}".format(is_active_user["err"]))
        return JsonResponse({
            "post_success": False,
            "post_msg": "UsersPanelApiDeleteRow(): {}".format(is_active_user["err"]),
        })

    ## Check active admin
    is_active_admin = user_is_active_admin(request.user)
    if is_active_admin["success"] == True:
        pass
    else:
        return JsonResponse({
            "post_success": False,
            "post_msg": "UsersPanelApiDeleteRow(): {}".format(is_active_admin["err"]),
        })

    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UsersPanelApiDeleteRow():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    ## Make sure user_id is convertable to a unsign int
    try:
        user_id = json_blob['user_id']

        try:
            user_id = int(user_id)
        except Exception as e:
            return JsonResponse({
                "post_success": False,
                "post_msg": "user_id cannot be converted to an int: '{}'".format(user_id),
            })

        if user_id <= 0:
            return JsonResponse({
                "post_success": False,
                "post_msg": "user_id is less than or equal to zero: '{}'".format(user_id),
            })
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UsersPanelApiDeleteRow():\n\nThe POSTed json obj does not have the following variable: {}".format(e),
        })

    ## Get user row reference
    try:
        user_row = Users.objects.get(user_id=user_id)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UsersPanelApiDeleteRow():\n\nFailed to get user object reference from database for user_id '{}': '{}'".format(user_id, e),
        })

    ## Check that there is no UserPermissions rows associated with given user_id
    try:
        if UserPermissions.objects.filter(user__user_id__exact=user_id).exists():
            return JsonResponse({
                "post_success": False,
                "post_msg": "Error: UsersPanelApiDeleteRow():\n\nCannot delete User '{}', there are rows in User Permissions that is associated with the User\n(Please delete the associated User Permissions first)".format(user_row.login),
            })
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UsersPanelApiDeleteRow(): {}".format(e),
        })

    ## Remove the permission row
    try:
        user_row.delete()
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UsersPanelApiDeleteRow():\n\nFailed to remove user_id '{}' from database: '{}'".format(user_id, e),
        })

    return JsonResponse({
        "post_success": True,
        "post_msg": "",
    })

def UsersPanelApiUpdateData(request):
    ## Read the json request body
    try:
        json_blob = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "Error: UsersPanelApiUpdateData():\n\nUnable to load request.body as a json object: {}".format(e),
        })

    id = json_blob['id']
    table = json_blob['table']
    column = json_blob['column']
    new_value = json_blob['new_value']

    ## Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: UsersPanelApiUpdateData(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "UsersPanelApiUpdateData():\n\nUNAUTHENTICATE USER!",
            "post_data": None,
        })

    ## Check active user
    is_active_user = user_is_active_user(request.user)
    if is_active_user["success"] == True:
        pass
    else:
        print("UsersPanelApiUpdateData(): {}".format(is_active_user["err"]))
        return JsonResponse({
            "post_success": False,
            "post_msg": "UsersPanelApiUpdateData(): {}".format(is_active_user["err"]),
            "post_data": None,
        })

    ## Check active admin
    is_active_admin = user_is_active_admin(request.user)
    if is_active_admin["success"] == True:
        pass
    else:
        return JsonResponse({
            "post_success": False,
            "post_msg": "UsersPanelApiUpdateData(): {}".format(is_active_admin["err"]),
            "post_data": None,
        })

    ## Save the data
    if table == "Users":

        ## Make sure new_value is convertable to its respective data type. If it's a string, make sure it's not empty or just whitespace
        if column == "Active_User":
            if new_value == "True":
                new_value = True
            elif new_value == "False":
                new_value = False
            else:
                print("Error: UsersPanelApiUpdateData(): Unable to convert new_value '{}' to bool type, did not save the value".format(new_value))
                return JsonResponse({
                    "post_success": False,
                    "post_msg": "Error: UsersPanelApiUpdateData():\n\nUnable to convert new_value '{}' to bool type, did not save the value".format(new_value),
                })
        else:
            try:
                new_value = str(new_value)
                new_value = new_value.strip()
                if new_value == "":
                    print("Error: UsersPanelApiUpdateData(): new_value cannot be a empty string")
                    return JsonResponse({
                        "post_success": False,
                        "post_msg": "Error: UsersPanelApiUpdateData():\n\nnew_value cannot be a empty string",
                    })
            except Exception as e:
                print("Error: UsersPanelApiUpdateData(): Unable to convert new_value '{}' to str type, did not save the value: {}".format(new_value), e)
                return JsonResponse({
                    "post_success": False,
                    "post_msg": "Error: UsersPanelApiUpdateData():\n\nUnable to convert new_value '{}' to str type, did not save the value: {}".format(new_value, e),
                })

        ## Save the value
        try:
            row = Users.objects.get(user_id=id)
            if column == "Active_User":
                row.active_user = new_value
                row.save()
                print("Api Log: UsersPanelApiUpdateData(): Client '{}' has successfully updated Users. For User_ID '{}' updated the {}.{} to '{}'".format(remote_user, id, table, column, new_value))
                return JsonResponse({
                    "post_success": True,
                    "post_msg": "",
                })
            if column == "First_Name":
                row.first_name = new_value
                row.save()
                print("Api Log: UsersPanelApiUpdateData(): Client '{}' has successfully updated Users. For User_ID '{}' updated the {}.{} to '{}'".format(remote_user, id, table, column, new_value))
                return JsonResponse({
                    "post_success": True,
                    "post_msg": "",
                })
            if column == "Last_Name":
                row.last_name = new_value
                row.save()
                print("Api Log: UsersPanelApiUpdateData(): Client '{}' has successfully updated Users. For User_ID '{}' updated the {}.{} to '{}'".format(remote_user, id, table, column, new_value))
                return JsonResponse({
                    "post_success": True,
                    "post_msg": "",
                })
            else:
                print("Warning: UsersPanelApiUpdateData(): Updating to column '{}' for table '{}' not supported\n".format(column, table))
                return JsonResponse({
                    "post_success": False,
                    "post_msg": "Warning: UsersPanelApiUpdateData():\n\nUpdating to column '{}' for table '{}' not supported\n".format(column, table),
                })
        except Exception as e:
            print("Error: UsersPanelApiUpdateData(): While trying to update {}.{} record to '{}' for user_id '{}': {}".format(table, column, new_value, id, e))
            return JsonResponse({
                "post_success": False,
                "post_msg": "Error: UsersPanelApiUpdateData():\n\nWhile trying to update {}.{} record to '{}' for user_id '{}': {}".format(table, column, new_value, id, e),
            })

    print("Warning: UsersPanelApiUpdateData(): Did not know what to do with the request. The request:\n\nid: '{}'\n table: '{}'\n column: '{}'\n new_value: '{}'\n".format(id, table, column, new_value))
    return JsonResponse({
        "post_success": False,
        "post_msg": "Warning: UsersPanelApiUpdateData():\n\nDid not know what to do with the request. The request:\n\nid: '{}'\n table: '{}'\n column: '{}'\n new_value: '{}'\n".format(id, table, column, new_value),
    })
