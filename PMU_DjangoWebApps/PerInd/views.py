from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from django.views.generic import TemplateView
from django.views import generic
from .models import *
from datetime import datetime
from django.utils import timezone
import pytz # For converting datetime objects from one timezone to another timezone
from django.db.models import Q
# Create your views here.

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

# Check if remote user is admin and is active
def user_is_active_admin(username):
    try:
        admin_query = Admins.objects.filter(
            user__login=username,
            active=True, # Filters for active Admins
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

# Given a record id, checks if user has permission to edit the record
def user_has_permission_to_edit(username, record_id):
    try:
        category_info = get_user_category_permissions(username)
        category_id_permission_list = category_info["pk_list"]
        record_category_info = IndicatorData.objects.values('indicator__category__category_id', 'indicator__category__category_name').get(record_id=record_id) # Take a look at https://docs.djangoproject.com/en/3.0/ref/models/querysets/ on "values()" section
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
            raise # re-raise the error that happend in get_user_category_permissions(), because ["success"] is only False when an exception happens in get_user_category_permissions()
        else: # Else successful query, but no permissions results found
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
    template_name = 'template.home.html'

class AboutPageView(TemplateView):
    template_name = 'template.about.html'

class ContactPageView(TemplateView):
    template_name = 'template.contact.html'

# Method Flowchart (the order of execution) for generic.ListView
#     setup()
#     dispatch()
#     http_method_not_allowed()
#     get_template_names()
#     get_queryset()
#     get_context_object_name()
#     get_context_data()
#     get()
#     render_to_response()
class WebGridPageView(generic.ListView):
    template_name = 'PerInd.template.webgrid.html'
    context_object_name = 'indicator_data_entries'

    paginate_by = 12

    req_success = False
    category_permissions = []
    err_msg = ""

    req_sort_dir = ""
    req_sort_by = ""
    
    uniq_titles = []
    uniq_years = []
    uniq_fiscal_years = []
    uniq_months = []
    uniq_categories = []
    
    req_title_list_filter = []
    req_yr_list_filter = [] # Calendar Year
    req_mn_list_filter = []
    req_fy_list_filter = [] # Fiscal Year
    req_cat_list_filter = [] # Category

    ctx_pagination_param = ""
    
    title_sort_anchor_GET_param = ""
    yyyy_sort_anchor_GET_param = ""
    mm_sort_anchor_GET_param = ""
    fy_yyyy_sort_anchor_GET_param = ""
    cat_sort_anchor_GET_param = ""

    client_is_admin = False

    def get_queryset(self):
        
        # Collect GET url parameter info
        temp_sort_dir = self.request.GET.get('SortDir')
        if (temp_sort_dir is not None and temp_sort_dir != '') and (temp_sort_dir == 'asc' or temp_sort_dir == 'desc'):
            self.req_sort_dir = temp_sort_dir

        temp_sort_by = self.request.GET.get('SortBy')
        if (temp_sort_by is not None and temp_sort_by != ''):
            self.req_sort_by = temp_sort_by
           
        self.req_title_list_filter = self.request.GET.getlist('TitleListFilter')
        self.req_yr_list_filter = self.request.GET.getlist('YYYYListFilter')
        self.req_mn_list_filter = self.request.GET.getlist('MMListFilter')
        self.req_fy_list_filter = self.request.GET.getlist('FiscalYYYYListFilter')
        self.req_cat_list_filter = self.request.GET.getlist('CategoriesListFilter')

        # Get list authorized Categories of Indicator Data, and log the category_permissions
        is_admin = user_is_active_admin(self.request.user)
        if is_admin["success"] == True:
            # Is admin, so unrestricted list of cetegories
            user_cat_permissions = get_admin_category_permissions()
            # test_cat_ids = {
            #     1: "Unknown",
            #     2: "RRM - Arterial Maintenance",
            #     3: "Bridges",
            #     4: "Ferries",
            #     5: "Fleet",
            #     6: "Permits",
            #     7: "TPM - RIS",
            #     8: "SIM - Sidewalks",
            #     9: "Communications",
            #     10: "RRM - Street Maintenance",
            #     11: "TPM",
            #     12: "Traffic Ops",
            # }
            # user_cat_permissions = {"success": True, "pk_list": [each for each in test_cat_ids], "category_names": [test_cat_ids[each] for each in test_cat_ids]}

            self.client_is_admin = True
        elif is_admin["success"] == False:
            # If not admin, do standard filter with categories
            user_cat_permissions = get_user_category_permissions(self.request.user)
            self.client_is_admin = False
        elif is_admin["success"] is None:
            self.req_success = False
            self.err_msg = "Exception: WebGridPageView(): get_queryset(): {}".format(is_admin["err"])
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

        # Default filters on the WebGrid dataset
        try:
            indicator_data_entries = IndicatorData.objects.filter(
                indicator__category__pk__in=category_pk_list, # Filters for authorized Categories
                indicator__active=True, # Filters for active Indicator titles
                year_month__yyyy__gt=timezone.now().year-4, # Filter for only last four year, "yyyy_gt" is "yyyy greater than"
            )
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: WebGridPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return IndicatorData.objects.none()

        # Get dropdown list values (Don't move this function, needs to be after the default filtered dataset, to pull unique title, years and months)
        try:
            self.uniq_titles = indicator_data_entries.order_by('indicator__indicator_title').values('indicator__indicator_title').distinct()

            self.uniq_years = indicator_data_entries.order_by('year_month__yyyy').values('year_month__yyyy').distinct()

            self.uniq_months = indicator_data_entries.order_by('year_month__mm').values('year_month__mm').distinct()

            # self.uniq_fiscal_years = list(set([ each.year_month.fiscal_yyyy for each in indicator_data_entries ])) # set(list()) to get distinct values out of the list, but it will be unordered! But seems to work for now, since it happens to result in a sorted order, I will let this sit for now

            if self.client_is_admin == True:
                self.uniq_categories = indicator_data_entries.order_by('indicator__category__category_name').values('indicator__category__category_name').distinct()
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: WebGridPageView(): get_queryset(): {}".format(e)
            print(self.err_msg)
            return IndicatorData.objects.none()

        #refrencee: https://stackoverflow.com/questions/5956391/django-objects-filter-with-list 
        # Filter dataset from Dropdown list
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
        # ## Filter by Fiscal Years
        # if len(self.req_fy_list_filter) >= 1:
        #     try:
        #         qs = Q()
        #         for each_fiscal_yr in self.req_fy_list_filter:
        #             each_fiscal_yr = int(each_fiscal_yr)
        #             # funky query here to implement the logic that year x jan-june, means Fiscal Year = x, and year x july-dec, means Fiscal Year = x + 1.
        #             # In other words, any year x with month in [7,8,9,10,11,12] is FY = x+1, and any year x with month in [1,2,3,4,5,6] is FY = x
        #             qs = qs | ( ( Q(year_month__mm__in=[1,2,3,4,5,6]) & Q(year_month__yyyy=each_fiscal_yr) ) | ( Q(year_month__mm__in=[7,8,9,10,11,12]) & Q(year_month__yyyy=each_fiscal_yr-1) ) )
        #         indicator_data_entries = indicator_data_entries.filter(qs)
        #     except Exception as e:
        #         self.req_success = False
        #         self.err_msg = "Exception: WebGridPageView(): get_queryset(): Fiscal Years Filtering: {}".format(e)
        #         print(self.err_msg)
        #         return IndicatorData.objects.none()
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

        # Filter dataset from sort direction and sort column
        try:
            ## Handles sorting by Property here, such as sorting by Fiscal Year
            ### It's okay to use YYYY as the sort fiscal year here. Since Fiscal Year doesn't actually exists in the database model, it's hard to do the sort. And since Fiscal Year is alwaya a fix offset from Calendar Year, sorting by Calendar Year will sort the Fiscal Year correctly. In effect, we are sorting Fiscal Year by proxy(proxy through sorting Calendar Year)
            if self.req_sort_by == 'year_month__fiscal_yyyy':
                # if self.req_sort_dir == "asc":
                #     # # Order the month first for neatness
                #     # indicator_data_entries = indicator_data_entries.order_by('year_month__mm')
                #     # Ref: https://stackoverflow.com/questions/8478494/ordering-django-queryset-by-a-property
                #     # and Ref: https://stackoverflow.com/questions/8966538/syntax-behind-sortedkey-lambda
                #     indicator_data_entries = sorted(indicator_data_entries, key=lambda each_rec: each_rec.year_month.fiscal_yyyy)
                # elif self.req_sort_dir == "desc":
                #     # # Order the month first for neatness
                #     # indicator_data_entries = indicator_data_entries.order_by('-year_month__mm')
                #     # Ref: https://www.w3schools.com/python/ref_func_sorted.asp
                #     indicator_data_entries = sorted(indicator_data_entries, key=lambda each_rec: each_rec.year_month.fiscal_yyyy, reverse=True)
                # else:
                #     self.req_success = False
                #     self.err_msg = "Exception: WebGridPageView(): get_queryset(): Unrecognized option for self.req_sort_dir: {}".format(self.req_sort_dir)
                #     print(self.err_msg)
                #     return IndicatorData.objects.none()
                print()
            # Default sort
            elif self.req_sort_by == '':
                # # Default sort it by Fiscal Year Desc and to show latest year first then to older years
                # indicator_data_entries = sorted(indicator_data_entries, key=lambda each_rec: each_rec.year_month.fiscal_yyyy, reverse=True)
                print()
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

        self.req_success = True
        return indicator_data_entries

    def get_context_data(self, **kwargs):
        try:
            # Call the base implementation first to get a context
            context = super().get_context_data(**kwargs)

            # Construct current context filter and sort GET param string, for front end to keep states
            ctx_title_filter_param = ""
            ctx_yyyy_filter_param = ""
            ctx_mm_filter_param = ""
            ctx_fiscal_yyyy_filter_param = ""
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
                ctx_fiscal_yyyy_filter_param = "{}FiscalYYYYListFilter={}&".format(ctx_fiscal_yyyy_filter_param, each)
            if self.client_is_admin == True:
                for each in self.req_cat_list_filter:
                    ctx_cat_filter_param = "{}CategoriesListFilter={}&".format(ctx_cat_filter_param, each)

            ## Construct <a></a> GET parameter for the sorting columns
            ### Defaults
            ctx_title_sort_dir = "SortDir=asc&"
            ctx_yyyy_sort_dir = "SortDir=asc&"
            ctx_mm_sort_dir = "SortDir=asc&"
            ctx_fiscal_yyyy_sort_dir = "SortDir=asc&"
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
            elif self.req_sort_by == 'year_month__fiscal_yyyy':
                if self.req_sort_dir == 'asc':
                    ctx_fiscal_yyyy_sort_dir = "SortDir=desc&"
            elif self.req_sort_by == 'indicator__category__category_name':
                if self.req_sort_dir == 'asc':
                    ctx_cat_sort_dir = "SortDir=desc&"


            self.title_sort_anchor_GET_param = "SortBy=indicator__indicator_title&{}{}{}{}{}{}".format(ctx_title_sort_dir, ctx_title_filter_param, ctx_yyyy_filter_param, ctx_mm_filter_param, ctx_fiscal_yyyy_filter_param, ctx_cat_filter_param)
            self.yyyy_sort_anchor_GET_param = "SortBy=year_month__yyyy&{}{}{}{}{}{}".format(ctx_yyyy_sort_dir, ctx_title_filter_param, ctx_yyyy_filter_param, ctx_mm_filter_param, ctx_fiscal_yyyy_filter_param, ctx_cat_filter_param)
            self.mm_sort_anchor_GET_param = "SortBy=year_month__mm&{}{}{}{}{}{}".format(ctx_mm_sort_dir, ctx_title_filter_param, ctx_yyyy_filter_param, ctx_mm_filter_param, ctx_fiscal_yyyy_filter_param, ctx_cat_filter_param)
            self.fy_yyyy_sort_anchor_GET_param = "SortBy=year_month__fiscal_yyyy&{}{}{}{}{}{}".format(ctx_fiscal_yyyy_sort_dir, ctx_title_filter_param, ctx_yyyy_filter_param, ctx_mm_filter_param, ctx_fiscal_yyyy_filter_param, ctx_cat_filter_param)
            self.cat_sort_anchor_GET_param = "SortBy=indicator__category__category_name&{}{}{}{}{}{}".format(ctx_cat_sort_dir, ctx_title_filter_param, ctx_yyyy_filter_param, ctx_mm_filter_param, ctx_fiscal_yyyy_filter_param, ctx_cat_filter_param)
            ### At this point, your self.title_sort_anchor_GET_param is something like
            ### "SortBy=indicator__indicator_title&SortDir=desc&title_list=Facebook&title_list=Instagram&yr_list=2019&yr_list=2020&mn_list=2&mn_list=1"

            ## Construct the context filter and sort param (This is your master param, as it contains all the Sort By and Filter By information, except Paging By information. The paging part of the param is handled in the front end PerInd.template.webgrid.html)
            self.ctx_pagination_param = "SortBy={}&SortDir={}&{}{}{}{}{}".format(self.req_sort_by, self.req_sort_dir, ctx_title_filter_param, ctx_yyyy_filter_param, ctx_mm_filter_param, ctx_fiscal_yyyy_filter_param, ctx_cat_filter_param)


            # Finally, setting the context variables
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
            context["fy_yyyy_sort_anchor_GET_param"] = self.fy_yyyy_sort_anchor_GET_param
            context["cat_sort_anchor_GET_param"] = self.cat_sort_anchor_GET_param

            context["ctx_pagination_param"] = self.ctx_pagination_param

            context["client_is_admin"] = self.client_is_admin

            return context
        except Exception as e:
            self.req_success = False
            self.err_msg = "Exception: get_context_data(): {}".format(e)
            context = super().get_context_data(**kwargs)
            context["req_success"] = self.req_success
            context["err_msg"] = self.err_msg
            print(self.err_msg)
            context["indicator_data_entries"] = IndicatorData.objects.none()

            context["category_permissions"] = ""

            context["sort_dir"] = ""
            context["sort_by"] = ""

            context["uniq_titles"] = []
            context["uniq_years"] = []
            context["uniq_months"] = []
            context["uniq_categories"] = []

            context["ctx_title_list_filter"] = ""
            context["ctx_yr_list_filter"] = ""
            context["ctx_mn_list_filter"] = ""
            context["ctx_cat_list_filter"] = ""

            context["title_sort_anchor_GET_param"] = ""
            context["yyyy_sort_anchor_GET_param"] = ""
            context["mm_sort_anchor_GET_param"] = ""
            context["fy_yyyy_sort_anchor_GET_param"] = ""
            context["cat_sort_anchor_GET_param"] = ""

            context["ctx_pagination_param"] = ""

            context["client_is_admin"] = False
            return context

# Post request
def SavePerIndDataApi(request):
    id = request.POST.get('id', '')
    table = request.POST.get('table', '')
    column = request.POST.get('column', '')
    new_value = request.POST.get('new_value', '')

    # Authenticate User
    remote_user = None
    if request.user.is_authenticated:
        remote_user = request.user.username
    else:
        print('Warning: SavePerIndDataApi(): UNAUTHENTICATE USER!')
        return JsonResponse({
            "post_success": False,
            "post_msg": "SavePerIndDataApi():\n\nUNAUTHENTICATE USER!",
        })

    # Authenticate permission for user
    user_perm_chk = user_has_permission_to_edit(remote_user, id)
    if user_perm_chk["success"] == False:
        print("Warning: SavePerIndDataApi(): USER '{}' has no permission to edit record #{}!".format(remote_user, id))
        return JsonResponse({
            "post_success": False,
            "post_msg": "SavePerIndDataApi():\n\nUSER '{}' has no permission to edit record #{}: SavePerIndDataApi(): {}".format(remote_user, id, user_perm_chk["err"]),
        })


    # Make sure new_value is convertable to float
    try:
        new_value = float(new_value)
    except Exception as e:
        print("Warning: SavePerIndDataApi(): Unable to convert new_value '{}' as float type, did not save the value".format(new_value))
        return JsonResponse({
            "post_success": False,
            "post_msg": "Warning: SavePerIndDataApi():\n\nUnable to convert new_value '{}' as float type, did not save the value".format(new_value),
        })

    if table == "IndicatorData":
        row = IndicatorData.objects.get(record_id=id)

        if column=="val":
            try:
                row.val = new_value

                # Update [last updated by] to current remote user, also make sure it's active user
                user_obj = Users.objects.get(login=remote_user, active_user=True) # Will throw exception if no user is found with the criteria: "Users matching query does not exist.""
                row.update_user = user_obj

                # Update [updated date] to current time
                # updated_timestamp = datetime.now() # Give 'naive' local time, which happens to be EDT on my home dev machine
                updated_timestamp = timezone.now() # Give 'time zone awared' datetime, but backend is UTC
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
                print("Error: SavePerIndDataApi(): Something went wrong while trying to save to the database: {}".format(e))
                return JsonResponse({
                    "post_success": False,
                    "post_msg": "Error: SavePerIndDataApi():\n\nSomething went wrong while trying to save to the database: {}".format(e),
                })

    print("Warning: SavePerIndDataApi(): Did not know what to do with the request. The request:\n\nid: '{}'\n table: '{}'\n column: '{}'\n new_value: '{}'\n".format(id, table, column, new_value))
    return JsonResponse({
        "post_success": False,
        "post_msg": "Warning: SavePerIndDataApi():\n\nDid not know what to do with the request. The request:\n\nid: '{}'\n table: '{}'\n column: '{}'\n new_value: '{}'\n".format(id, table, column, new_value),
    })

# Post request
def GetCsvApi(request):
    """
    Download WebGrid view with all current context as xlsx.
    Expects all the filter and sort context in the request. (Don't need pagination context)
    """
    import csv
    from io import StringIO

    dummy_in_mem_file = StringIO()
    csv_queryset = None

    # Collect GET url parameter info
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
    req_fy_list_filter = request.POST.getlist('FiscalYYYYListFilter[]')

    print("req_sort_dir: {}".format(req_sort_dir))
    print("req_sort_by: {}".format(req_sort_by))
    print("req_title_list_filter: {}".format(req_title_list_filter))
    print("req_yr_list_filter: {}".format(req_yr_list_filter))
    print("req_mn_list_filter: {}".format(req_mn_list_filter))
    print("req_fy_list_filter: {}".format(req_fy_list_filter))

    # Authenticate User
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

    # Get list authorized Categories of Indicator Data, and log the category_permissions
    user_cat_permissions = get_user_category_permissions(request.user)
    if user_cat_permissions["success"] == False:
        return JsonResponse({
            "post_success": True,
            "post_msg": "GetCsvApi(): Fail to get a list of authorized category permissions",
            "post_data": None,
        })
    category_pk_list = user_cat_permissions["pk_list"]

    # Default filters on the WebGrid dataset
    try:
        csv_queryset = IndicatorData.objects.filter(
            indicator__category__pk__in=category_pk_list, # Filters for authorized Categories
            indicator__active=True, # Filters for active Indicator titles
            year_month__yyyy__gt=timezone.now().year-4, # Filter for only last four year, "yyyy_gt" is "yyyy greater than"
        )
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "GetCsvApi(): Failed to get any data from queryset: {}\n\nErr Msg: {}".format(user_perm_chk["err"], e),
            "post_data": None,
        })

    # Query for the queryset with matching filter and sort criteria
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
            for each_fiscal_yr in req_fy_list_filter:
                each_fiscal_yr = int(each_fiscal_yr)
                # funky query here to implement the logic that year x jan-june, means Fiscal Year = x, and year x july-dec, means Fiscal Year = x + 1.
                # In other words, any year x with month in [7,8,9,10,11,12] is FY = x+1, and any year x with month in [1,2,3,4,5,6] is FY = x
                qs = qs | ( ( Q(year_month__mm__in=[1,2,3,4,5,6]) & Q(year_month__yyyy=each_fiscal_yr) ) | ( Q(year_month__mm__in=[7,8,9,10,11,12]) & Q(year_month__yyyy=each_fiscal_yr-1) ) )
            csv_queryset = csv_queryset.filter(qs)
        except Exception as e:
            return JsonResponse({
                "post_success": False,
                "post_msg": "GetCsvApi(): Failed to filter FY from queryset\n\nErr Msg: {}".format(e),
                "post_data": None,
            })

    # Filter dataset from sort direction and sort column
    try:
        if req_sort_by == 'year_month__fiscal_yyyy':
            if req_sort_dir == "asc":
                csv_queryset = sorted(csv_queryset, key=lambda each_rec: each_rec.year_month.fiscal_yyyy)
            elif req_sort_dir == "desc":
                csv_queryset = sorted(csv_queryset, key=lambda each_rec: each_rec.year_month.fiscal_yyyy, reverse=True)
            else:
                return JsonResponse({
                    "post_success": False,
                    "post_msg": "GetCsvApi(): Failed to sort by FY from queryset, unrecognize req_sort_dir: {}".format(req_sort_dir),
                    "post_data": None,
                })
        # Default sort
        elif req_sort_by == '':
            # Default sort it by Fiscal Year Desc and to show latest year first then to older years
            csv_queryset = sorted(csv_queryset, key=lambda each_rec: each_rec.year_month.fiscal_yyyy, reverse=True)
        else:
            if req_sort_dir == "asc":
                csv_queryset = csv_queryset.order_by(req_sort_by)
            elif req_sort_dir == "desc":
                csv_queryset = csv_queryset.order_by('-{}'.format(req_sort_by))
            else:
                return JsonResponse({
                    "post_success": False,
                    "post_msg": "GetCsvApi(): Failed to sort by FY from queryset, unrecognize req_sort_dir: {}".format(req_sort_dir),
                    "post_data": None,
                })
    except Exception as e:
        return JsonResponse({
            "post_success": False,
            "post_msg": "GetCsvApi(): Failed to sort from queryset\n\nErr Msg: {}".format(e),
            "post_data": None,
        })

    # Convert to CSV
    writer = csv.writer(dummy_in_mem_file)
    writer.writerow(['Indicator Title', 'Fiscal Year', 'Month', 'Indicator Value', 'Updated Date', 'Last Updated By', 'Category',])
    for each in csv_queryset:
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
            each.indicator,
            each.year_month.fiscal_yyyy,
            month_name,
            each.val,
            each.updated_date.strftime("%m/%d/%Y"),
            each.update_user,
            each.indicator.category.category_name,
        ]
        writer.writerow(eachrow)
        # print(eachrow)

    return JsonResponse({
        "post_success": True,
        "post_msg": "GetCsvApi(): Success, check for variable 'post_data' in the response JSON for the csv file",
        "post_data": dummy_in_mem_file.getvalue(),
    })