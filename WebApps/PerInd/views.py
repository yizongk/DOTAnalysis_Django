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
from WebAppsMain.api_decorators import post_request_decorator
## Create your views here.


def get_admin_category_permissions():
    try:
        user_permissions_list = Category.objects.using('PerInd').all()
        return {
            "pk_list": [x.category_id for x in user_permissions_list],
            "category_names": [x.category_name for x in user_permissions_list],
        }
    except Exception as e:
        raise ValueError(f"get_admin_category_permissions(): {e}")


def get_user_category_permissions(username):
    try:
        user_permissions_list = UserPermissions.objects.using('PerInd').filter(user__login=username)
        return {
            "pk_list": [x.category.category_id for x in user_permissions_list],
            "category_names": [x.category.category_name for x in user_permissions_list],
        }
    except Exception as e:
        raise ValueError(f"get_user_category_permissions(): {e}")


## Check if remote user is admin and is active
def user_is_active_admin(username):
    try:
        admin_query = Admins.objects.using('PerInd').filter(
            user__login=username,
            active=True, ## Filters for active Admins
        )
        if admin_query.count() == 1:
            return True
        else:
            return False
    except Exception as e:
        raise ValueError(f"user_is_active_admin(): {e}")


def user_is_active_user(username):
    try:
        user_query = Users.objects.using('PerInd').filter(
            login=username,
            active_user=True, ## Filters for active users
        )
        if user_query.count() == 1:
            return True
        else:
            return False
    except Exception as e:
        raise ValueError(f"user_is_active_user(): {e}")


## Given a record id, checks if user has permission to edit the record
def user_has_permission_to_edit(username, record_id):
    try:
        is_active_admin = user_is_active_admin(username)
        if is_active_admin:
            category_info = get_admin_category_permissions()
        else:
            ## If not admin, do standard filter with categories
            category_info = get_user_category_permissions(username)

        category_id_permission_list = category_info["pk_list"]

        record_category_info        = IndicatorData.objects.using('PerInd').values('indicator__category__category_id', 'indicator__category__category_name').get(record_id=record_id) ## Take a look at https://docs.djangoproject.com/en/3.0/ref/models/querysets/ on "values()" section
        record_category_id          = record_category_info["indicator__category__category_id"]
        if len(category_id_permission_list) != 0:
            if record_category_id in category_id_permission_list:
                return True

        return False
    except Exception as e:
        raise ValueError(f"user_has_permission_to_edit(): {e}")


class HomePageView(TemplateView):
    template_name   = 'PerInd.template.home.html'
    get_success     = True
    get_error       = None
    client_is_admin = False

    def get_context_data(self, **kwargs):
        if not user_is_active_user(self.request.user):
            self.get_success    = False
            self.get_error      = f"'{self.request.user}' is not an active user"

        ## Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context["get_success"]      = self.get_success
        context["get_error"]        = self.get_error
        context["client_is_admin"]  = user_is_active_admin(self.request.user)
        return context


class AboutPageView(TemplateView):
    template_name   = 'PerInd.template.about.html'
    get_success     = True
    get_error       = None
    client_is_admin = False

    def get_context_data(self, **kwargs):
        if not user_is_active_user(self.request.user):
            self.get_success    = False
            self.get_error      = f"'{self.request.user}' is not an active user"

        context = super().get_context_data(**kwargs)
        context["get_success"]      = self.get_success
        context["get_error"]        = self.get_error
        context["client_is_admin"]  = user_is_active_admin(self.request.user)
        return context


class ContactPageView(TemplateView):
    template_name   = 'PerInd.template.contact.html'
    get_success     = True
    get_error       = None
    client_is_admin = False

    def get_context_data(self, **kwargs):
        if not user_is_active_user(self.request.user):
            self.get_success    = False
            self.get_error      = f"'{self.request.user}' is not an active user"

        context = super().get_context_data(**kwargs)
        context["get_success"]      = self.get_success
        context["get_error"]        = self.get_error
        context["client_is_admin"]  = user_is_active_admin(self.request.user)
        return context


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
    template_name       = 'PerInd.template.webgrid.html'
    context_object_name = 'indicator_data_entries'

    get_success     = True
    get_error       = ""
    client_is_admin = False

    category_permissions = []

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

    def get_queryset(self):
        try:
            if not user_is_active_user(self.request.user):
                raise ValueError(f"'{self.request.user}' is not an active user")

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
            self.client_is_admin = user_is_active_admin(self.request.user)
            if self.client_is_admin:
                user_cat_permissions = get_admin_category_permissions()

            else:
                ## If not admin, do standard filter with categories
                is_active_user = user_is_active_user(self.request.user)

                if is_active_user:
                    user_cat_permissions = get_user_category_permissions(self.request.user)
                else:
                    raise ValueError(f"User '{self.request.user}' is not an active user")

            category_pk_list            = user_cat_permissions["pk_list"]
            self.category_permissions   = user_cat_permissions["category_names"]

            ## Default filters on the WebGrid dataset
            indicator_data_entries = IndicatorData.objects.using('PerInd').filter(
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
                    self.get_success = False
                    self.get_error = "WebGridPageView(): get_queryset(): Titles Filtering: {}".format(e)
                    return None
            ## Filter by YYYYs
            if len(self.req_yr_list_filter) >= 1:
                try:
                    qs = Q()
                    for i in self.req_yr_list_filter:
                        qs = qs | Q(year_month__yyyy=i)
                    indicator_data_entries = indicator_data_entries.filter(qs)
                except Exception as e:
                    self.get_success = False
                    self.get_error = "WebGridPageView(): get_queryset(): Years Filtering: {}".format(e)
                    return None
            ## Filter by MMs
            if len(self.req_mn_list_filter) >= 1:
                try:
                    qs = Q()
                    for i in self.req_mn_list_filter:
                        qs = qs | Q(year_month__mm=i)
                    indicator_data_entries = indicator_data_entries.filter(qs)
                except Exception as e:
                    self.get_success = False
                    self.get_error = "WebGridPageView(): get_queryset(): Months Filtering: {}".format(e)
                    return None
            ## Filter by Fiscal Years
            if len(self.req_fy_list_filter) >= 1:
                try:
                    qs = Q()
                    for i in self.req_fy_list_filter:
                        qs = qs | Q(year_month__fiscal_year=i)
                    indicator_data_entries = indicator_data_entries.filter(qs)
                except Exception as e:
                    self.get_success = False
                    self.get_error = "WebGridPageView(): get_queryset(): Fiscal Years Filtering: {}".format(e)
                    return None
            ## Filter by Categories
            if self.client_is_admin == True:
                if len(self.req_cat_list_filter) >= 1:
                    try:
                        qs = Q()
                        for i in self.req_cat_list_filter:
                            qs = qs | Q(indicator__category__category_name=i)
                        indicator_data_entries = indicator_data_entries.filter(qs)
                    except Exception as e:
                        self.get_success = False
                        self.get_error = "WebGridPageView(): get_queryset(): Categories Filtering: {}".format(e)
                        return None

            ## Sort dataset from sort direction and sort column
            ## Default sort
            if self.req_sort_by == '':
                indicator_data_entries = indicator_data_entries.order_by('indicator__category__category_name', '-year_month__fiscal_year', '-year_month__mm', 'indicator__indicator_title')
            else:
                if self.req_sort_dir == "asc":
                    indicator_data_entries = indicator_data_entries.order_by(self.req_sort_by)
                elif self.req_sort_dir == "desc":
                    indicator_data_entries = indicator_data_entries.order_by('-{}'.format(self.req_sort_by))
                else:
                    self.get_success = False
                    self.get_error = "WebGridPageView(): get_queryset(): Unrecognized option for self.req_sort_dir: {}".format(self.req_sort_dir)
                    return None

            ## Get dropdown list values (Don't move this function, needs to be after the filtered and sorted dataset, to pull unique title, years and months base on current context)
            self.uniq_titles        = indicator_data_entries.order_by('indicator__indicator_title').values('indicator__indicator_title').distinct()
            self.uniq_years         = indicator_data_entries.order_by('year_month__yyyy').values('year_month__yyyy').distinct()
            self.uniq_months        = indicator_data_entries.order_by('year_month__mm').values('year_month__mm').distinct()
            self.uniq_fiscal_years  = indicator_data_entries.order_by('year_month__fiscal_year').values('year_month__fiscal_year').distinct()

            if self.client_is_admin == True:
                self.uniq_categories = indicator_data_entries.order_by('indicator__category__category_name').values('indicator__category__category_name').distinct()
        except Exception as e:
            self.get_success    = False
            self.get_error      = f"WebGridPageView(): get_queryset(): {e}"
            return IndicatorData.objects.using('PerInd').none()

        self.get_success = True
        return indicator_data_entries

    def get_context_data(self, **kwargs):
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
        context["get_success"]      = self.get_success
        context["get_error"]        = self.get_error
        context["client_is_admin"]  = self.client_is_admin

        context["category_permissions"] = self.category_permissions

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

        return context


## Post request
@post_request_decorator
def PerIndApiUpdateData(request, json_blob, remote_user):
    try:
        ## Check json request param is not empty string
        id          = json_blob['id']
        table       = json_blob['table']
        column      = json_blob['column']
        new_value   = json_blob['new_value']

        if type(id) is not int:
            raise ValueError(f"id must be int type. Current type is {type(id)}")

        if type(table) is not str:
            raise ValueError(f"table must be string type. Current type is {type(table)}")

        if type(column) is not str:
            raise ValueError(f"column must be string type. Current type is {type(column)}")

        if type(new_value) is not str:
            raise ValueError(f"new_value must be string type. Current type is {type(new_value)}")
        else:
            if float(new_value) < 0:
                raise ValueError(f"new_value cannot be negative: {new_value}")


        if id == "":
            raise ValueError(f"id cannot be an empty string")

        if table == "":
            raise ValueError(f"table cannot be an empty string")

        if column == "":
            raise ValueError(f"column cannot be an empty string")

        if new_value == "":
            raise ValueError(f"new_value cannot be an empty string")

        ## Make sure User is an active User
        is_active_user = user_is_active_user(request.user)
        if not is_active_user:
            raise ValueError(f"'{remote_user}' is not an active user!")

        ## Authenticate permission for user
        can_edit = user_has_permission_to_edit(remote_user, id)
        if not can_edit:
            raise ValueError(f"USER '{remote_user}' has no permission to edit record #{id}")

        ## Make sure new_value is convertable to float
        try:
            new_value = float(new_value)
        except Exception as e:
            raise ValueError(f"Unable to convert new_value '{new_value}' to float type, did not save the value: {e}")

        if table == "IndicatorData":
            row = IndicatorData.objects.using('PerInd').get(record_id=id)

            if column=="val":
                row.val = new_value

                ## Update [last updated by] to current remote user, also make sure it's active user
                user_obj = Users.objects.using('PerInd').get(login=remote_user, active_user=True) ## Will throw exception if no user is found with the criteria: "Users matching query does not exist.""
                row.update_user = user_obj

                ## Update [updated date] to current time
                ## updated_timestamp = datetime.now() ## Give 'naive' local time, which happens to be EDT on my home dev machine
                updated_timestamp = timezone.now() ## Give 'time zone awared' datetime, but backend is UTC
                row.updated_date = updated_timestamp

                local_updated_timestamp_str_response = updated_timestamp.astimezone(pytz.timezone('America/New_York')).strftime("%B %d, %Y, %I:%M %p")

                row.save(using='PerInd')

                return JsonResponse({
                    "post_success": True,
                    "post_msg": None,
                    "post_data": {
                        "value_saved"       : new_value,
                        "updated_timestamp" : local_updated_timestamp_str_response,
                        "updated_by"        : remote_user,
                    },
                })
            else:
                raise ValueError(f"The api does not support operation with this column: '{column}'")
        else:
            raise ValueError(f"The api does not support operation with this table: '{table}'")

        raise ValueError(f"Warning\n\n\Did not know what to do with the request. The request:\n\nid: '{id}'\n table: '{table}'\n column: '{column}'\n new_value: '{new_value}'\n")
    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"PerIndApiUpdateData(): {e}",
            "post_data"     : None,
        })


## Post request
@post_request_decorator
def PerIndApiGetCsv(request, json_blob, remote_user):
    """
    Download WebGrid view with all current context as xlsx.
    Expects all the filter and sort context in the request. (Don't need pagination context)
    """
    try:
        import csv
        from io import StringIO

        dummy_in_mem_file       = StringIO()
        csv_queryset            = None
        client_is_admin         = False

        ## Collect GET url parameter info
        req_sort_dir            = ""
        req_sort_by             = ""

        temp_sort_dir           = json_blob['SortDir']
        if (temp_sort_dir is not None and temp_sort_dir != '') and (temp_sort_dir == 'asc' or temp_sort_dir == 'desc'):
            req_sort_dir = temp_sort_dir

        temp_sort_by            = json_blob['SortBy']
        if (temp_sort_by is not None and temp_sort_by != ''):
            req_sort_by = temp_sort_by

        req_title_list_filter   = json_blob['TitleListFilter']
        req_yr_list_filter      = json_blob['YYYYListFilter']
        req_mn_list_filter      = json_blob['MMListFilter']
        req_fy_list_filter      = json_blob['FiscalYearListFilter']
        req_cat_list_filter     = json_blob['CategoriesListFilter']

        if type(req_title_list_filter) is not list:
            raise ValueError(f"req_title_list_filter must be a list: {type(req_title_list_filter)}")
        if type(req_yr_list_filter) is not list:
            raise ValueError(f"req_yr_list_filter must be a list: {type(req_yr_list_filter)}")
        if type(req_mn_list_filter) is not list:
            raise ValueError(f"req_mn_list_filter must be a list: {type(req_mn_list_filter)}")
        if type(req_fy_list_filter) is not list:
            raise ValueError(f"req_fy_list_filter must be a list: {type(req_fy_list_filter)}")
        if type(req_cat_list_filter) is not list:
            raise ValueError(f"req_cat_list_filter must be a list: {type(req_cat_list_filter)}")

        ## Get list authorized Categories of Indicator Data, and log the category_permissions
        client_is_admin = user_is_active_admin(request.user)
        if client_is_admin:
            user_cat_permissions = get_admin_category_permissions()
        else:
            ## If not admin, do standard filter with categories
            is_active_user = user_is_active_user(request.user)
            if is_active_user:
                user_cat_permissions = get_user_category_permissions(request.user)
            else:
                raise ValueError(f"User '{request.user}' is not an active user")

        ## Get list authorized Categories of Indicator Data, and log the category_permissions
        category_pk_list = user_cat_permissions["pk_list"]

        ## Default filters on the WebGrid dataset
        csv_queryset = IndicatorData.objects.using('PerInd').filter(
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

        ## Query for the queryset with matching filter and sort criteria
        ## Filter by Titles
        if len(req_title_list_filter) >= 1:
            try:
                qs = Q()
                for i in req_title_list_filter:
                    qs = qs | Q(indicator__indicator_title=i)
                csv_queryset = csv_queryset.filter(qs)
            except Exception as e:
                raise ValueError(f"Failed to filter Titles from queryset\n\nErr Msg: {e}")
        ## Filter by YYYYs
        if len(req_yr_list_filter) >= 1:
            try:
                qs = Q()
                for i in req_yr_list_filter:
                    qs = qs | Q(year_month__yyyy=i)
                csv_queryset = csv_queryset.filter(qs)
            except Exception as e:
                raise ValueError(f"Failed to filter YYYY from queryset\n\nErr Msg: {e}")
        ## Filter by MMs
        if len(req_mn_list_filter) >= 1:
            try:
                qs = Q()
                for i in req_mn_list_filter:
                    qs = qs | Q(year_month__mm=i)
                csv_queryset = csv_queryset.filter(qs)
            except Exception as e:
                raise ValueError(f"Failed to filter MM from queryset\n\nErr Msg: {e}")
        ## Filter by Fiscal Years
        if len(req_fy_list_filter) >= 1:
            try:
                qs = Q()
                for i in req_fy_list_filter:
                    qs = qs | Q(year_month__fiscal_year=i)
                csv_queryset = csv_queryset.filter(qs)
            except Exception as e:
                raise ValueError(f"Failed to filter FY from queryset\n\nErr Msg: {e}")
        ## Filter by Categories
        if client_is_admin == True:
            if len(req_cat_list_filter) >= 1:
                try:
                    qs = Q()
                    for i in req_cat_list_filter:
                        qs = qs | Q(indicator__category__category_name=i)
                    csv_queryset = csv_queryset.filter(qs)
                except Exception as e:
                    raise ValueError(f"Failed to filter Categories from queryset\n\nErr Msg: {e}")

        ## Sort dataset from sort direction and sort column
        ## Default sort
        if req_sort_by == '':
            csv_queryset = csv_queryset.order_by('indicator__category__category_name', '-year_month__fiscal_year', '-year_month__mm', 'indicator__indicator_title')
        else:
            if req_sort_dir == "asc":
                csv_queryset = csv_queryset.order_by(req_sort_by)
            elif req_sort_dir == "desc":
                csv_queryset = csv_queryset.order_by('-{}'.format(req_sort_by))
            else:
                raise ValueError(f"Failed to sort, unrecognize req_sort_dir: {req_sort_dir}")

        ## Convert to CSV
        writer = csv.writer(dummy_in_mem_file)
        writer.writerow(['Category', 'Indicator Title', 'Fiscal Year', 'Calendar Year', 'Month', 'Indicator Value', 'Units', 'Multiplier', 'Updated Date', 'Last Updated By', ])
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
                each.year_month.yyyy,
                month_name,
                each.val,
                each.indicator.unit.unit_type,
                each.indicator.val_multiplier.multiplier_scale,
                each.updated_date.strftime("%m/%d/%Y"),
                each.update_user,
            ]
            writer.writerow(eachrow)

        return JsonResponse({
            "post_success"  : True,
            "post_msg"      : None,
            "post_data"     : {
                "csv_bytes": dummy_in_mem_file.getvalue()
            },
        })
    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"PerIndApiGetCsv(): {e}",
            "post_data"     : None,
        })


## For admin access only
class PastDueIndicatorsPageView(generic.ListView):
    template_name       = 'PerInd.template.pastdueindicators.html'
    context_object_name = 'indicator_data_entries'

    get_success     = True
    get_error       = ""
    client_is_admin = False

    paginate_by = 24

    req_sort_dir = ""
    req_sort_by = ""

    uniq_categories = []

    req_cat_list_filter = [] ## Category

    ctx_pagination_param = ""

    cat_sort_anchor_GET_param = ""

    def get_queryset(self):
        ## Collect GET url parameter info
        try:
            if not user_is_active_user(self.request.user):
                raise ValueError(f"'{self.request.user}' is not an active user")

            ## Check for Active Admins
            self.client_is_admin = user_is_active_admin(self.request.user)
            if not self.client_is_admin:
                raise ValueError(f"{self.request.user} is not an admin and is not authorized to see this page")

            temp_sort_dir = self.request.GET.get('SortDir')
            if (temp_sort_dir is not None and temp_sort_dir != '') and (temp_sort_dir == 'asc' or temp_sort_dir == 'desc'):
                self.req_sort_dir = temp_sort_dir

            temp_sort_by = self.request.GET.get('SortBy')
            if (temp_sort_by is not None and temp_sort_by != ''):
                self.req_sort_by = temp_sort_by

            self.req_cat_list_filter = self.request.GET.getlist('CategoriesListFilter')

            ## Use python to process the queryset to find a list of Indicator_Data.Records_IDs that meet the Past-Due-Criteria
            ## Criteria for past due, last month entered is at least three months in the past (Updated_Date = '1899-12-30', means no data was entered, it is also our default 'NULL/Empty' date)
            base_data_qs = IndicatorData.objects.using('PerInd').filter(
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
            unique_ind_ids = base_data_qs.order_by('indicator_id').values('indicator_id').distinct()
            for each_ind_id in unique_ind_ids:
                ind_id_related = base_data_qs.filter(indicator_id__exact=each_ind_id['indicator_id']).order_by('indicator_id', '-year_month__yyyy', '-year_month__mm')

                for each_row in ind_id_related:
                    ## Assumes the ind_id_related doens't contain any records tracking future dates greater than current month and current year, else will return error. Also assumes ind_id_related is sorted by ('indicator_id', '-year_month__yyyy', '-year_month__mm'), but doesn't check nor will return error.
                    if ( each_row.year_month.yyyy > timezone.now().year ) or ( each_row.year_month.yyyy == timezone.now().year and each_row.year_month.mm > timezone.now().month ):
                        self.get_success = False
                        self.get_error = "PastDueIndicatorsPageView(): get_queryset(): ind_id_related queryset contains records tracking dates greater than current month and current year, the record tracks yyyy: '{}' and mm: '{}'".format(each_row.year_month.yyyy, each_row.year_month.mm)
                        return None

                    ## Indicator could be up-to-date, current record is for entry for the last three month (Counting current month, last month, and the month before)
                    if (
                        ( each_row.year_month.yyyy == timezone.now().year     and timezone.now().month - each_row.year_month.mm < 3 ) or
                        ( each_row.year_month.yyyy == timezone.now().year - 1 and   (
                                                                                        (timezone.now().month == 1 and each_row.year_month.mm >= 11) or
                                                                                        (timezone.now().month == 2 and each_row.year_month.mm == 12)
                                                                                    )
                        )
                    ): ## (yyyy = current year and month difference is within 2) OR (yyyy = last year and month difference is within 10)
                        if each_row.updated_date.date().year != datetime(1899, 12, 30).date().year:
                            # Indicator is up-to-date, abort loop and go scan the next Indicator
                            break
                        else:
                            # check the next record
                            continue
                    ## Indicator is past-dued (current record is for entry over two months ago, before current month and last month), find the latest record where data was entered.
                    else:
                        if each_row.updated_date.date().year != datetime(1899, 12, 30).date().year:
                            ## Found latest record where data was entered, break loop and scan the next Indicator
                            past_due_record_id_list.append(each_row.record_id)
                            break
                        else:
                            # check the next record
                            continue

            ## Use the following query in SSMS to verify what is shown on the website is actaully outdated records by more than 2 month and shows just the latest record that was entered for each indicator title
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

            ## Requery db to match up with the list of Indicator_Data.Records_IDs to pass to the client
            indicator_data_entries = IndicatorData.objects.using('PerInd').filter(
                pk__in=past_due_record_id_list,
            )

            ## refrencee: https://stackoverflow.com/questions/5956391/django-objects-filter-with-list
            ## Filter dataset from Dropdown list
            ## Filter by Categories
            if len(self.req_cat_list_filter) >= 1:
                qs = Q()
                for i in self.req_cat_list_filter:
                    qs = qs | Q(indicator__category__category_name=i)
                indicator_data_entries = indicator_data_entries.filter(qs)

            ## Sort dataset from sort direction and sort column
            ## Default sort
            if self.req_sort_by == '':
                indicator_data_entries = indicator_data_entries.order_by('indicator__category__category_name', '-year_month__fiscal_year', '-year_month__mm', 'indicator__indicator_title')
            else:
                if self.req_sort_dir == "asc":
                    indicator_data_entries = indicator_data_entries.order_by(self.req_sort_by)
                elif self.req_sort_dir == "desc":
                    indicator_data_entries = indicator_data_entries.order_by('-{}'.format(self.req_sort_by))
                else:
                    self.get_success = False
                    self.get_error = "PastDueIndicatorsPageView(): get_queryset(): Unrecognized option for self.req_sort_dir: {}".format(self.req_sort_dir)
                    return None

            ## Get dropdown list values (Don't move this function, needs to be after the filtered and sorted dataset, to pull unique title, years and months base on current context)
            self.uniq_categories = indicator_data_entries.order_by('indicator__category__category_name').values('indicator__category__category_name').distinct()
        except Exception as e:
            self.get_success    = False
            self.get_error      = f"PastDueIndicatorsPageView(): get_queryset(): {e}"
            return IndicatorData.objects.using('PerInd').none()

        self.get_success = True
        return indicator_data_entries

    def get_context_data(self, **kwargs):
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
        context["get_success"]      = self.get_success
        context["get_error"]        = self.get_error
        context["client_is_admin"]  = self.client_is_admin

        context["sort_dir"] = self.req_sort_dir
        context["sort_by"] = self.req_sort_by

        context["uniq_categories"] = self.uniq_categories
        context["ctx_cat_list_filter"] = self.req_cat_list_filter
        context["cat_sort_anchor_GET_param"] = self.cat_sort_anchor_GET_param
        context["ctx_pagination_param"] = self.ctx_pagination_param

        return context


class AdminPanelPageView(generic.ListView):
    template_name   = 'PerInd.template.adminpanel.html'

    get_success     = True
    get_error       = ""
    client_is_admin = False

    def get_queryset(self):
        try:
            ## Check for Active User
            is_active_user = user_is_active_user(self.request.user)
            if not is_active_user:
                raise ValueError(f"{self.request.user} is not an active user and is not authorized to see this page")

            ## Check for Active Admins
            self.client_is_admin = user_is_active_admin(self.request.user)
            if not self.client_is_admin:
                raise ValueError(f"{self.request.user} is not an admin and is not authorized to see this page")
        except Exception as e:
            self.get_success    = False
            self.get_error      = f"AdminPanelPageView(): get_queryset(): {e}"
            return

        self.get_success = True
        return

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["get_success"]      = self.get_success
        context["get_error"]        = self.get_error
        context["client_is_admin"]  = self.client_is_admin

        return context


class UserPermissionsPanelPageView(generic.ListView):
    template_name       = 'PerInd.template.userpermissionspanel.html'
    context_object_name = 'permission_data_entries'

    get_success     = True
    get_error       = ""
    client_is_admin = False

    users_list = []
    categories_list = []
    def get_queryset(self):
        try:
            ## Check for Active User
            is_active_user = user_is_active_user(self.request.user)
            if not is_active_user:
                raise ValueError(f"{self.request.user} is not an active user and is not authorized to see this page")

            ## Check for Active Admins
            self.client_is_admin = user_is_active_admin(self.request.user)
            if not self.client_is_admin:
                raise ValueError(f"{self.request.user} is not an admin and is not authorized to see this page")

            ## Get the permissions data
            permission_data_entries = UserPermissions.objects.using('PerInd').all().order_by('user__login')

            ## Get the active users login list
            user_objs = Users.objects.using('PerInd').filter(
                active_user=True
            ).order_by('login')

            self.users_list = user_objs

            ## Get the category list
            category_objs = Category.objects.using('PerInd').all().order_by('category_name')
            self.categories_list = category_objs

        except Exception as e:
            self.get_success    = False
            self.get_error      = f"UserPermissionsPanelPageView(): get_queryset(): {e}"
            return UserPermissions.objects.using('PerInd').none()

        self.get_success = True
        return permission_data_entries

    def get_context_data(self, **kwargs):
        ## Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        ## Finally, setting the context variables
        ## Add my own variables to the context for the front end to shows
        context["get_success"]      = self.get_success
        context["get_error"]        = self.get_error
        context["client_is_admin"]  = self.client_is_admin

        context["users_list"]       = self.users_list
        context["categories_list"]  = self.categories_list
        return context


## Post request - for single cell edits
@post_request_decorator
def UserPermissionsPanelApiUpdateData(request, json_blob, remote_user):
    try:
        ## Check active user
        is_active_user = user_is_active_user(request.user)
        if not is_active_user:
            raise ValueError(f"{request.user} is not an active user and is not authorized to see this page")

        ## Check active admin
        is_active_admin = user_is_active_admin(request.user)
        if not is_active_admin:
            raise ValueError(f"{request.user} is not an admin and is not authorized to see this page")

        id          = json_blob['id']
        table       = json_blob['table']
        column      = json_blob['column']
        new_value   = json_blob['new_value']

        if type(id) is not int:
            raise ValueError(f"id must be int: {type(id)}")
        if type(table) is not str:
            raise ValueError(f"table must be str: {type(table)}")
        if type(column) is not str:
            raise ValueError(f"column must be str: {type(column)}")
        if type(new_value) is not str:
            raise ValueError(f"new_value must be str: {type(new_value)}")

        ## Save the data
        if table == "UserPermissions":
            ## Make sure new_value is convertable to its respective data type
            if column == "Active":
                if new_value == 'True':
                    new_value = True
                elif new_value == 'False':
                    new_value = False
                else:
                    raise ValueError(f"new_value '{new_value}' is not a valid value for {table}.{column}")
            else:
                raise ValueError(f"'{column}' is not an editable column for table '{table}'")

            ## Save the value
            row = UserPermissions.objects.using('PerInd').get(user_permission_id=id)
            row.active = new_value
            row.save(using='PerInd')

            return JsonResponse({
                "post_success"  : True,
                "post_msg"      : None,
                "post_data"     : None,
            })
        else:
            raise ValueError(f"update to table '{table}' is not implemented")

    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"UserPermissionsPanelApiUpdateData(): {e}",
            "post_data"     : None,
        })


## For form add row
@post_request_decorator
def UserPermissionsPanelApiAddRow(request, json_blob, remote_user):
    """
        Expects the post request to post a JSON object, and that it will contain login_selection and category_selection. Like so:
        {
            login_selection: "Some value",
            category_selection: "Some other value"
        }
        Will create a new row in the Permissions table with the selected login and category
    """

    try:
        ## Check active user
        is_active_user = user_is_active_user(request.user)
        if not is_active_user:
            raise ValueError(f"{request.user} is not an active user and is not authorized to see this page")

        ## Check active admin
        is_active_admin = user_is_active_admin(request.user)
        if not is_active_admin:
            raise ValueError(f"{request.user} is not an admin and is not authorized to see this page")

        ## Check login_selection and category_selection is not empty string
        login_selection     = json_blob['login_selection']
        category_selection  = json_blob['category_selection']

        if login_selection == "":
            raise ValueError(f"login_selection cannot be an empty string")

        if category_selection == "":
            raise ValueError(f"category_selection cannot be an empty string")

        ## Check that the login_selection and category_selection exists
        if not Users.objects.using('PerInd').filter(login__exact=login_selection, active_user__exact=True).exists():
            raise ValueError(f"'{login_selection}' doesn't exists or it's not an active user")

        if not Category.objects.using('PerInd').filter(category_name__exact=category_selection).exists():
            raise ValueError(f"'{category_selection}' doesn't exists as a Category")

        ## Check for duplication of login and category
        if UserPermissions.objects.using('PerInd').filter(user__login__exact=login_selection, category__category_name__exact=category_selection).exists():
            raise ValueError(f"'{login_selection}' already has access to '{category_selection}'")

        ## Create the row!
        user_obj        = Users.objects.using('PerInd').get(login=login_selection, active_user=True)
        category_obj    = Category.objects.using('PerInd').get(category_name=category_selection)
        new_permission  = UserPermissions(user=user_obj, category=category_obj)
        new_permission.save(using='PerInd')

        return JsonResponse({
            "post_success"  : True,
            "post_msg"      : None,
            "post_data"     : {
                "permission_id": new_permission.user_permission_id,
                "first_name": user_obj.first_name,
                "last_name": user_obj.last_name,
                "active_user": f"{user_obj.active_user}",
                "login": user_obj.login,
                "category_name": category_obj.category_name,
            },
        })
    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"UserPermissionsPanelApiAddRow(): {e}",
            "post_data"     : None,
        })


## For JS datatable delete row
@post_request_decorator
def UserPermissionsPanelApiDeleteRow(request, json_blob, remote_user):
    """
        Expects the post request to post a JSON object, and that it will contain user_permission_id. Like so:
        {
            user_permission_id: "Some value"
        }
        Will delete row in the Permissions table with the given user_permission_id
    """
    try:
        ## Check active user
        is_active_user = user_is_active_user(request.user)
        if not is_active_user:
            raise ValueError(f"{request.user} is not an active user and is not authorized to see this page")

        ## Check active admin
        is_active_admin = user_is_active_admin(request.user)
        if not is_active_admin:
            raise ValueError(f"{request.user} is not an admin and is not authorized to see this page")

        ## Make sure user_permission_id is convertable to a unsign int
        user_permission_id = json_blob['user_permission_id']

        if type(user_permission_id) is not str:
            raise ValueError(f"'user_permission_id' must be a str: {type(user_permission_id)}")
        elif not user_permission_id.isnumeric():
            raise ValueError(f"'user_permission_id' must be a numeric str: '{user_permission_id}'")

        user_permission_id = int(user_permission_id)

        ## Remove the permission row
        permission_row = UserPermissions.objects.using('PerInd').get(user_permission_id=user_permission_id)
        permission_row.delete()

        return JsonResponse({
            "post_success"  : True,
            "post_msg"      : None,
            "post_data"     : None,
        })
    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"UserPermissionsPanelApiDeleteRow(): {e}",
            "post_data"     : None,
        })


class UsersPanelPageView(generic.ListView):
    template_name       = 'PerInd.template.userspanel.html'
    context_object_name = 'users_data_entries'

    client_is_admin = False
    get_success     = True
    get_error       = ""

    def get_queryset(self):
        try:
            ## Check for Active User
            is_active_user = user_is_active_user(self.request.user)
            if not is_active_user:
                raise ValueError(f"{self.request.user} is not an active user and is not authorized to see this page")

            ## Check for Active Admins
            self.client_is_admin = user_is_active_admin(self.request.user)
            if not self.client_is_admin:
                raise ValueError(f"{self.request.user} is not an admin and is not authorized to see this page")

            ## Get the permissions data
            users_data_entries = Users.objects.using('PerInd').all().order_by('login')
        except Exception as e:
            self.get_success    = False
            self.get_error      = f"UsersPanelPageView(): get_queryset(): {e}"
            return Users.objects.using('PerInd').none()

        self.get_success = True
        return users_data_entries

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["get_success"]      = self.get_success
        context["get_error"]        = self.get_error
        context["client_is_admin"]  = self.client_is_admin
        return context


@post_request_decorator
def UsersPanelApiAddRow(request, json_blob, remote_user):
    """
        Expects the post request to post a JSON object, and that it will contain first_name_input, last_name_input and login_input. Like so:
        {
            first_name_input: "Some value",
            last_name_input: "Some value",
            login_input: "Some value",
        }
        Will create a new row in the Users table with the given first name, last name and login. Default the active_user to True
    """
    try:
        ## Check active user
        is_active_user = user_is_active_user(request.user)
        if not is_active_user:
            raise ValueError(f"{request.user} is not an active user and is not authorized to see this page")

        ## Check active admin
        is_active_admin = user_is_active_admin(request.user)
        if not is_active_admin:
            raise ValueError(f"{request.user} is not an admin and is not authorized to see this page")

        ## Check json request param is not empty string
        first_name_input    = json_blob['first_name_input']
        last_name_input     = json_blob['last_name_input']
        login_input         = json_blob['login_input']

        if type(first_name_input) is not str:
            raise ValueError(f"first_name_input must be a string: {type(first_name_input)}")
        if type(last_name_input) is not str:
            raise ValueError(f"last_name_input must be a string: {type(last_name_input)}")
        if type(login_input) is not str:
            raise ValueError(f"login_input must be a string: {type(login_input)}")

        if first_name_input == "":
            raise ValueError(f"first_name_input cannot be an empty string")
        if last_name_input == "":
            raise ValueError(f"last_name_input cannot be an empty string")
        if login_input == "":
            raise ValueError(f"login_input cannot be an empty string")

        ## Check for duplication of login
        if Users.objects.using('PerInd').filter(login__exact=login_input).exists():
            raise ValueError(f"'{login_input}' already exists in the Users table")

        ## Create the row!
        new_user = Users(first_name=first_name_input, last_name=last_name_input, login=login_input, active_user=True)
        new_user.save(using='PerInd')

        return JsonResponse({
            "post_success"  : True,
            "post_msg"      : None,
            "post_data"     : {
                "user_id": new_user.user_id,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name,
                "active_user": new_user.active_user,
                "login": new_user.login,
            },
        })
    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"UsersPanelApiAddRow(): {e}",
            "post_data"     : None,
        })


@post_request_decorator
def UsersPanelApiDeleteRow(request, json_blob, remote_user):
    """
        Expects the post request to post a JSON object, and that it will contain user_id. Like so:
        {
            user_id: "Some value"
        }
        Will delete row in the Users table with the given user_id.

        Delete will fail if there are any UserPermissions record associated with the Users.
    """
    try:
        ## Check active user
        is_active_user = user_is_active_user(request.user)
        if not is_active_user:
            raise ValueError(f"{request.user} is not an active user and is not authorized to see this page")

        ## Check active admin
        is_active_admin = user_is_active_admin(request.user)
        if not is_active_admin:
            raise ValueError(f"{request.user} is not an admin and is not authorized to see this page")

        ## Make sure user_id is convertable to a unsign int
        user_id = json_blob['user_id']

        try:
            user_id = int(user_id)
        except Exception as e:
            raise ValueError(f"user_id cannot be converted to an int: '{user_id}'")

        ## Get user row reference
        user_row = Users.objects.using('PerInd').get(user_id=user_id)

        ## Check that there is no UserPermissions rows associated with given user_id
        if UserPermissions.objects.using('PerInd').filter(user__user_id__exact=user_id).exists():
            raise ValueError(f"Cannot delete User '{user_row.login}', there are rows in User Permissions that is associated with the User\n(Please delete the associated User Permissions first)")

        ## Remove the permission row
        user_row.delete()

        return JsonResponse({
            "post_success"  : True,
            "post_msg"      : None,
            "post_data"     : None,
        })
    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"UsersPanelApiDeleteRow(): {e}",
            "post_data"     : None,
        })


@post_request_decorator
def UsersPanelApiUpdateData(request, json_blob, remote_user):
    try:
        ## Check active user
        is_active_user = user_is_active_user(request.user)
        if not is_active_user:
            raise ValueError(f"{request.user} is not an active user and is not authorized to see this page")

        ## Check active admin
        is_active_admin = user_is_active_admin(request.user)
        if not is_active_admin:
            raise ValueError(f"{request.user} is not an admin and is not authorized to see this page")

        id          = json_blob['id']
        table       = json_blob['table']
        column      = json_blob['column']
        new_value   = json_blob['new_value']

        if type(id) is not str:
            raise ValueError(f"id must be a str type: {type(id)}")
        if type(table) is not str:
            raise ValueError(f"table must be a str type: {type(table)}")
        if type(column) is not str:
            raise ValueError(f"column must be a str type: {type(column)}")
        if type(new_value) is not str:
            raise ValueError(f"new_value must be a str type: {type(new_value)}")

        ## Save the data
        if table == "Users":
            ## Make sure new_value is convertable to its respective data type. If it's a string, make sure it's not empty or just whitespace
            if column == "Active_User":
                if new_value == "True":
                    new_value = True
                elif new_value == "False":
                    new_value = False
                else:
                    raise ValueError(f"Unable to convert new_value '{new_value}' to bool type, did not save the value")
            else:
                new_value = str(new_value)
                new_value = new_value.strip()
                if new_value == "":
                    raise ValueError(f"new_value cannot be a empty string")

            ## Save the value
            row = Users.objects.using('PerInd').get(user_id=id)
            if column == "Active_User":
                row.active_user = new_value
                row.save(using='PerInd')
            elif column == "First_Name":
                row.first_name = new_value
                row.save(using='PerInd')
            elif column == "Last_Name":
                row.last_name = new_value
                row.save(using='PerInd')
            else:
                raise ValueError(f"Updating to column '{column}' for table '{table}' not supported")
        else:
            raise ValueError(f"Unrecognize table: '{table}'")

        return JsonResponse({
            "post_success"  : True,
            "post_msg"      : None,
            "post_data"     : None,
        })
    except Exception as e:
        return JsonResponse({
            "post_success"  : False,
            "post_msg"      : f"UsersPanelApiUpdateData(): {e}",
            "post_data"     : None,
        })
