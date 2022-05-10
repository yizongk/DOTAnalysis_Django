from .models import *
from WebAppsMain.settings import TEST_WINDOWS_USERNAME
from WebAppsMain.testing_utils import HttpPostTestCase, HttpGetTestCase
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

# Create your tests here.


DEFAULT_CATEGORY = 'Communications'


def get_or_create_user(windows_username=TEST_WINDOWS_USERNAME):
    """create or get an user and return the user object. Defaults to TEST_WINDOWS_USERNAME as the user"""
    try:
        user_obj = Users.objects.using('PerInd').get_or_create(
            login=windows_username
            ,first_name=windows_username
            ,last_name=windows_username
        )[0]
        user_obj.active_user=True
        user_obj.save(using='PerInd')

        return user_obj
    except Exception as e:
        raise ValueError(f"get_or_create_user(): {e}")


def grant_admin_status(windows_username=TEST_WINDOWS_USERNAME):
    """create or get an user and set it up with admin status and return the user object. Defaults to TEST_WINDOWS_USERNAME as the user"""
    try:
        user = get_or_create_user(windows_username=windows_username)
        user.active_user=True
        user.save(using='PerInd')

        admin = Admins.objects.using('PerInd').get_or_create(
            user=user
        )[0]
        admin.active=True
        admin.save(using='PerInd')

        return user
    except Exception as e:
        raise ValueError(f"grant_admin_status(): {e}")


def remove_admin_status(windows_username=TEST_WINDOWS_USERNAME):
    """removes the admin status of an user"""
    try:
        user = get_or_create_user(windows_username=windows_username)
        user.save(using='PerInd')

        admin = Admins.objects.using('PerInd').get_or_create(
            user=user
        )[0]
        admin.active=False
        admin.save(using='PerInd')

        return user
    except Exception as e:
        raise ValueError(f"remove_admin_status(): {e}")


def grant_active_user_status(windows_username=TEST_WINDOWS_USERNAME):
    """Set user as active"""
    try:
        user = get_or_create_user(windows_username=windows_username)
        user.active_user = True
        user.save(using='PerInd')
    except Exception as e:
        raise ValueError(f"grant_active_user_status(): {e}")


def remove_active_user_status(windows_username=TEST_WINDOWS_USERNAME):
    """Set user as inactive"""
    try:
        user = get_or_create_user(windows_username=windows_username)
        user.active_user = False
        user.save(using='PerInd')
    except Exception as e:
        raise ValueError(f"remove_active_user_status(): {e}")


def set_up_permissions(windows_username=TEST_WINDOWS_USERNAME, categories=[DEFAULT_CATEGORY]):
    """
        set up permissions for a user. If user is admin, the permissions added will probably mean nothing.

        @windows_username is self explanatory, just one name
        @categories should be a list of string category
    """
    try:
        for category in categories:

            category_obj = Category.objects.using('PerInd').get(
                category_name__exact=category
            )

            user_obj = get_or_create_user(windows_username=windows_username)
            permission_obj = UserPermissions.objects.using('PerInd').get_or_create(
                user        = user_obj
                ,category   = category_obj
            )[0]
            permission_obj.active = True
            permission_obj.save(using="PerInd")

    except Exception as e:
        raise ValueError(f"set_up_permissions(): {e}")


def tear_down_permissions(windows_username=TEST_WINDOWS_USERNAME):
    """remove all permissions for an user. If user is admin, the permissions removed will probably mean nothing."""
    try:
        permissions = UserPermissions.objects.using('PerInd').filter(
            user__login__exact=windows_username
        )

        for each in permissions:
            each.delete(using='PerInd')
    except Exception as e:
        raise ValueError(f"tear_down_permissions_for_user(): {e}")


def tear_down(windows_username=TEST_WINDOWS_USERNAME):
    """Removes admin status of @windows_username, and set all its permissions to inactive. Defaults to TEST_WINDOWS_USERNAME"""
    try:
        remove_admin_status(windows_username=windows_username)
        tear_down_permissions(windows_username=windows_username)
    except Exception as e:
        raise ValueError(f"tear_down(): {e}")


class TestViewPagesResponse(HttpGetTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        set_up_permissions()

        self.regular_views = [
            'perind_home_view',
            'perind_about_view',
            'perind_contact_view',
            'perind_webgrid_view',
        ]

        self.admin_views = [
            'perind_pastdueindicators',
            'perind_adminpanel',
            'perind_userpermissionspanel',
            'perind_userspanel',
        ]

        self.additional_context_requirements = [
            {
                'view'                      : 'perind_webgrid_view'
                ,'additional_context_keys'  : [
                                                'indicator_data_entries'
                                                ,'category_permissions'
                                                ,'sort_dir'
                                                ,'sort_by'
                                                ,'uniq_titles'
                                                ,'uniq_years'
                                                ,'uniq_fiscal_years'
                                                ,'uniq_months'
                                                ,'uniq_categories'
                                                ,'ctx_title_list_filter'
                                                ,'ctx_yr_list_filter'
                                                ,'ctx_mn_list_filter'
                                                ,'ctx_fy_list_filter'
                                                ,'ctx_cat_list_filter'
                                                ,'title_sort_anchor_GET_param'
                                                ,'yyyy_sort_anchor_GET_param'
                                                ,'mm_sort_anchor_GET_param'
                                                ,'fiscal_year_sort_anchor_GET_param'
                                                ,'cat_sort_anchor_GET_param'
                                                ,'ctx_pagination_param'
                                            ]
                ,'qa_fct'                   : None
            }
            ## The below are admin views
            ,{
                'view'                      : 'perind_pastdueindicators'
                ,'additional_context_keys'  : [
                                                'indicator_data_entries'
                                                ,'sort_dir'
                                                ,'sort_by'
                                                ,'uniq_categories'
                                                ,'ctx_cat_list_filter'
                                                ,'cat_sort_anchor_GET_param'
                                                ,'ctx_pagination_param'
                                            ]
                ,'qa_fct'                   : None
            }
            ,{
                'view'                      : 'perind_userpermissionspanel'
                ,'additional_context_keys'  : [
                                                'permission_data_entries'
                                                ,'users_list'
                                                ,'categories_list'
                                            ]
                ,'qa_fct'                   : self.__assert_additional_context_qa_manage_permissions
            }
            ,{
                'view'                      : 'perind_userspanel'
                ,'additional_context_keys'  : [
                                                'users_data_entries'
                                            ]
                ,'qa_fct'                   : self.__assert_additional_context_qa_manage_users
            }
        ]

    @classmethod
    def tearDownClass(self):
        tear_down()

    def __assert_additional_context_qa_manage_permissions(self, response):
        ## Make sure permission_data_entries has ALL the permission records, since this api is an admin api
        permission_data_entries = response.context_data['permission_data_entries']
        from_api_permissions    = set(each.user_permission_id   for each in permission_data_entries)
        required_permissions    = set(each.user_permission_id   for each in UserPermissions.objects.using('PerInd').filter(active=True))
        self.assertEqual(sorted(from_api_permissions), sorted(required_permissions)
            ,f"perind_userpermissionspanel: context variable permission_data_entries either has more data than allowed ({from_api_permissions - required_permissions}) or has less data than allowed ({required_permissions - from_api_permissions})")

        from_api_users_list         = set(each.user_id      for each in response.context_data['users_list'])
        from_api_categories_list    = set(each.category_id  for each in response.context_data['categories_list'])

        required_users_list         = set(each.user_id      for each in Users.objects.using('PerInd').filter(active_user=True))
        required_categories_list    = set(each.category_id  for each in Category.objects.using('PerInd').all())

        self.assertEqual(sorted(from_api_users_list), sorted(required_users_list)
            ,f"perind_userpermissionspanel: context variable users_list either has more data than allowed ({from_api_users_list - required_users_list}) or has less data than allowed ({required_users_list - from_api_users_list})")
        self.assertEqual(sorted(from_api_categories_list), sorted(required_categories_list)
            ,f"perind_userpermissionspanel: context variable categories_list either has more data than allowed ({from_api_categories_list - required_categories_list}) or has less data than allowed ({required_categories_list - from_api_categories_list})")

    def __assert_additional_context_qa_manage_users(self, response):
        ## Make sure users_data_entries has ALL the user records, since this api is an admin api
        users_data_entries      = response.context_data['users_data_entries']
        from_api_users_data     = set(each.user_id for each in users_data_entries)
        required_users_data     = set(each.user_id for each in Users.objects.using('PerInd').all())
        self.assertEqual(from_api_users_data, required_users_data
            ,f"perind_userspanel: context variable users_data_entries either has more data than allowed ({from_api_users_data - required_users_data}) or has less data than allowed ({required_users_data - from_api_users_data})")

    def test_views_response_status_200(self):
        """Test normal user"""
        remove_admin_status()
        self.assert_response_status_200()

        """Test admin user"""
        grant_admin_status()
        self.assert_response_status_200()

    def test_views_response_user_admin_restriction(self):
        """Test inactive user (Normal), should have NO access to regular or admin views"""
        remove_admin_status()
        remove_active_user_status()
        self.assert_inactive_user_no_access_on_normal_and_admin_view()

        """Test inactive user (Admin), should have NO access to regular or admin views"""
        grant_admin_status()
        remove_active_user_status()
        self.assert_inactive_user_no_access_on_normal_and_admin_view()

        """Test active user (Normal), should only have access to regular views"""
        grant_active_user_status()
        remove_admin_status()
        self.assert_user_access_on_normal_and_admin_view()

        """Test active user (Admin), should have access to regular and admin views"""
        grant_active_user_status()
        grant_admin_status()
        self.assert_admin_access_on_normal_and_admin_view()

    def test_views_response_data(self):
        """
            Test views to have the required GET request context data
            Some views have additional context data, need to test for those here
        """
        # Test normal user
        remove_admin_status()
        self.assert_additional_context_data(additional_requirements=self.additional_context_requirements)

        # Test admin user
        grant_admin_status()
        self.assert_additional_context_data(additional_requirements=self.additional_context_requirements)


class TestAPIPerIndApiUpdateData(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        set_up_permissions()
        self.user_obj                   = get_or_create_user()
        self.api_name                   = 'perind_update_data_api'
        self.post_response_json_key_specifications = [
            {'name': 'value_saved'          , 'null': False}
            ,{'name': 'updated_timestamp'   , 'null': False}
            ,{'name': 'updated_by'          , 'null': False}
        ]

        self.valid_id                   = IndicatorData.objects.using('PerInd').filter(indicator__category__category_name__exact=DEFAULT_CATEGORY, indicator__active=True).order_by('record_id')[0].record_id
        self.valid_table                = 'IndicatorData'
        self.valid_column               = 'val'
        self.valid_new_value            = '10.1'

        self.record                     = IndicatorData.objects.using('PerInd').get(record_id=self.valid_id)
        self.old_val                    = self.record.val

        self.valid_payloads = [
            {
                'id'        : self.valid_id,
                'table'     : self.valid_table,
                'column'    : self.valid_column,
                'new_value' : self.valid_new_value,
            },
        ]

    @classmethod
    def tearDownClass(self):
        self.record.val = self.old_val
        self.record.save(using='PerInd')
        tear_down()

    def test_with_valid_data(self):
        for payload in self.valid_payloads:
            self.assert_post_with_valid_payload_is_success(payload=payload)

            ## Check if data was saved correctly
            saved_object = IndicatorData.objects.using('PerInd').get(record_id=self.valid_id)

            self.assert_post_key_update_equivalence(key_name=payload['column'], key_value=float(payload['new_value'])    , db_value=saved_object.val)

            ## Update updated by user, and updated_date
            self.assertTrue(  (timezone.now() - saved_object.updated_date).total_seconds() < 10,
                f"[updated_date] didn't save correctly: '{saved_object.updated_date.strftime('%Y-%m-%d %H:%M:%S')}' input-->database '{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}'. Cannot exceed more than 10 seconds difference" )
            self.assert_post_key_update_equivalence(key_name="update_user", key_value=self.user_obj.user_id, db_value=saved_object.update_user.user_id)

    def test_data_validation(self):
        f"""Testing {self.api_name} data validation"""

        ## For PotholeData
        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name    # Accepted type
            "id"                # str   -> string formated int
            ,"table"            # str   -> must be in this list ['IndicatorData']
            ,"column"           # str   -> must be in this list ['val']
            ,"new_value"        # str   -> string formatted float
        ]
        for param_name in parameters:

            if param_name == 'id':
                valid   = [self.valid_id]
                invalid = ['a', -12, None, True, '']
            elif param_name == 'table':
                valid   = [self.valid_table]
                invalid = ['a', 1, 2.3, -12, None, False, '']
            elif param_name == 'column':
                valid   = [self.valid_column]
                invalid = ['a', 1, 2.3, -12, None, False, '']
            elif param_name == 'new_value':
                valid   = [self.valid_new_value]
                invalid = ['a', 1, 2.3, -12, None, False, '']
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPIPerIndApiGetCsv(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        set_up_permissions()
        self.user_obj                   = get_or_create_user()
        self.api_name                   = 'get_csv_cur_ctx_api'
        self.post_response_json_key_specifications = [
            {'name': 'csv_bytes', 'null': False}
        ]

        self.SortDir                = "asc"
        self.SortBy                 = "indicator__indicator_title"
        self.TitleListFilter        = [
                                        IndicatorList.objects.using('PerInd').filter(category__category_name__exact=DEFAULT_CATEGORY, active=True)[0].indicator_title
                                    ]
        self.YYYYListFilter         = [
                                        "2020"
                                    ]
        self.MMListFilter           = [
                                        "8"
                                    ]
        self.FiscalYearListFilter   = [
                                        "2021"
                                    ]
        self.CategoriesListFilter   = [
                                        DEFAULT_CATEGORY
                                    ]

        self.valid_payloads = [
            {
                "SortDir"               : self.SortDir,
                "SortBy"                : self.SortBy,
                "TitleListFilter"       : self.TitleListFilter,
                "YYYYListFilter"        : self.YYYYListFilter,
                "MMListFilter"          : self.MMListFilter,
                "FiscalYearListFilter"  : self.FiscalYearListFilter,
                "CategoriesListFilter"  : self.CategoriesListFilter
            },
        ]

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_with_valid_data(self):
        for payload in self.valid_payloads:
            self.assert_post_with_valid_payload_is_success(payload=payload)

    def test_data_validation(self):
        f"""Testing {self.api_name} data validation"""

        ## For PotholeData
        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name        # Accepted type
            "SortDir"               # str   -> ['asc', 'desc']
            ,"SortBy"               # str   -> one of the column name referenced from indicator_data object
            ,"TitleListFilter"      # list  -> must be a list of active indicator titles
            ,"YYYYListFilter"       # list  -> str formatted 4 digit years
            ,"MMListFilter"         # list  -> str formatted 1 or 2 digit months
            ,"FiscalYearListFilter" # list  -> str formatted 4 digit years
            ,"CategoriesListFilter" # list  -> must be a list of valid categories
        ]
        for param_name in parameters:

            if param_name == 'SortDir':
                valid   = [self.SortDir]
                invalid = ['a', -12, True]
            elif param_name == 'SortBy':
                valid   = [self.SortBy]
                invalid = ['a', 1, 2.3, -12, False]
            elif param_name == 'TitleListFilter':
                valid   = [self.TitleListFilter]
                invalid = ['a', 1, 2.3, -12, None, False, '']
            elif param_name == 'YYYYListFilter':
                valid   = [self.YYYYListFilter]
                invalid = ['a', 1, 2.3, -12, None, False, '']
            elif param_name == 'MMListFilter':
                valid   = [self.MMListFilter]
                invalid = ['a', 1, 2.3, -12, None, False, '']
            elif param_name == 'FiscalYearListFilter':
                valid   = [self.FiscalYearListFilter]
                invalid = ['a', 1, 2.3, -12, None, False, '']
            elif param_name == 'CategoriesListFilter':
                valid   = [self.CategoriesListFilter]
                invalid = ['a', 1, 2.3, -12, None, False, '']
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPIUserPermissionsPanelApiUpdateData(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        set_up_permissions()
        self.api_name               = 'user_permissions_panel_api_update_data'
        self.post_response_json_key_specifications = []

        self.valid_permission_id    = UserPermissions.objects.using('PerInd').filter(
                                        user__login__exact=TEST_WINDOWS_USERNAME
                                    )[0].user_permission_id

        self.valid_table            = 'UserPermissions'
        self.valid_column           = 'Active'
        self.new_value              = 'True'

        self.valid_payloads = [
            {
                'id'        : self.valid_permission_id,
                'table'     : self.valid_table,
                'column'    : self.valid_column,
                'new_value' : self.new_value
            }
        ]

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_api_accept_only_admins(self):
        remove_admin_status()

        payload = self.valid_payloads[0]
        content = self.post_and_get_json_response(payload)

        self.assertTrue((content['post_success']==False) and ("not an admin" in content['post_msg']),
            f"api should have detected that user is not an admin and fail\n{content['post_msg']}")

    def test_with_valid_data(self):
        grant_admin_status()

        for payload in self.valid_payloads:
            self.assert_post_with_valid_payload_is_success(payload=payload)

            ## Check if data was saved correctly
            saved_object = UserPermissions.objects.using('PerInd').get(
                user_permission_id=self.valid_permission_id
            )

            self.assert_post_key_update_equivalence(key_name=payload['column'], key_value=payload['new_value'], db_value=str(saved_object.active))

    def test_data_validation(self):
        grant_admin_status()

        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name    # Accepted type
            'id'                # str/int -> string formatted int or int: primary key of a row in the Permission table
            ,'table'            # str -> Table name
            ,'column'           # str -> Column name of the table
            ,'new_value'        # str -> the new value to be saved
        ]
        for param_name in parameters:
            if param_name == 'id':
                valid   = [self.valid_permission_id]
                invalid = ['a', '-1', '-1.2', '11.567', '2.2', '4.45', 5.46, -1, None, False, True, '']
            elif param_name == 'table':
                valid   = [self.valid_table]
                invalid = [1, 2.3, False, None, 'sdf', '']
            elif param_name == 'column':
                valid   = [self.valid_column]
                invalid = ['a', 1, 2.3, '-1', '-1.2', '11.567', '2.2', '4.45', None, False, True, '']
            elif param_name == 'new_value':
                valid   = [self.new_value]
                invalid = ['a', '-1', '-1.2', '11.567', '2.2', '4.45', 1000, -1, None, False, True, '']
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPIUserPermissionsPanelApiAddRow(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        self.api_name               = 'user_permissions_panel_api_add_row'
        self.post_response_json_key_specifications = [
            {'name': 'permission_id'    , 'null': False}
            ,{'name': 'first_name'      , 'null': False}
            ,{'name': 'last_name'       , 'null': False}
            ,{'name': 'active_user'     , 'null': False}
            ,{'name': 'login'           , 'null': False}
            ,{'name': 'category_name'   , 'null': False}
        ]

        self.valid_login_selection      = TEST_WINDOWS_USERNAME
        self.valid_category_selection   = DEFAULT_CATEGORY

        self.valid_payloads = [
            {
                'login_selection'       : self.valid_login_selection,
                'category_selection'    : self.valid_category_selection,
            }
        ]

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_api_accept_only_admins(self):
        remove_admin_status()

        payload = self.valid_payloads[0]
        content = self.post_and_get_json_response(payload)

        self.assertTrue((content['post_success']==False) and ("not an admin" in content['post_msg']),
            f"api should have detected that user is not an admin and fail\n{content['post_msg']}")

    def test_with_valid_data(self):
        grant_admin_status()

        for payload in self.valid_payloads:
            tear_down_permissions() ## Remove the existing permission of our test user
            response_json = self.assert_post_with_valid_payload_is_success(payload=payload)

            ## Check if data was saved correctly
            saved_object = UserPermissions.objects.using('PerInd').get(
                user_permission_id=response_json['post_data']['permission_id']
            )

            self.assert_post_key_update_equivalence(key_name='login_selection', key_value=payload['login_selection'], db_value=str(saved_object.user.login))
            self.assert_post_key_update_equivalence(key_name='category_selection', key_value=payload['category_selection'], db_value=str(saved_object.category.category_name))
            self.assert_post_key_update_equivalence(key_name='active', key_value=True, db_value=str(saved_object.active))

    def test_data_validation(self):
        grant_admin_status()

        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name        # Accepted type
            'login_selection'       # str -> windows username
            ,'category_selection'   # str -> a category name
        ]
        for param_name in parameters:
            if param_name == 'login_selection':
                valid   = [self.valid_login_selection]
                invalid = ['a', 1, 2.3, '-1', '-1.2', '11.567', '2.2', '4.45', None, False, True, '']
            elif param_name == 'category_selection':
                valid   = [self.valid_category_selection]
                invalid = ['a', '-1', '-1.2', '11.567', '2.2', '4.45', 1000, -1, None, False, True, '']
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                tear_down_permissions() ## Remove the existing permission of our test user
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                tear_down_permissions() ## Remove the existing permission of our test user
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)


class TestAPIUserPermissionsPanelApiDeleteRow(HttpPostTestCase):
    @classmethod
    def setUpClass(self):
        tear_down()
        self.api_name               = 'user_permissions_panel_api_delete_row'
        self.post_response_json_key_specifications = []

        self.user_permission_id = None

        self.valid_payloads = [
            {
                'user_permission_id': None,
            }
        ]

    @classmethod
    def tearDownClass(self):
        tear_down()

    def test_api_accept_only_admins(self):
        remove_admin_status()

        payload = self.valid_payloads[0]
        content = self.post_and_get_json_response(payload)

        self.assertTrue((content['post_success']==False) and ("not an admin" in content['post_msg']),
            f"api should have detected that user is not an admin and fail\n{content['post_msg']}")

    def test_with_valid_data(self):
        grant_admin_status()

        for payload in self.valid_payloads:
            ## Set up a temp permission to delete
            set_up_permissions(windows_username=TEST_WINDOWS_USERNAME, categories=[DEFAULT_CATEGORY])
            self.valid_permission_id = str(UserPermissions.objects.using('PerInd').get(
                user__login=TEST_WINDOWS_USERNAME
                ,category__category_name=DEFAULT_CATEGORY
            ).user_permission_id)
            payload['user_permission_id'] = self.valid_permission_id
            response_json = self.assert_post_with_valid_payload_is_success(payload=payload)

            ## Check if data was deleted correctly
            try:
                saved_object = UserPermissions.objects.using('PerInd').get(user_permission_id=self.valid_permission_id)
            except ObjectDoesNotExist as e:
                ... ## Good, do nothing
            except Exception as e:
                raise ValueError(f"test_with_valid_data(): {e}")
            else:
                self.assertTrue(False, f"user_permission_id {saved_object.user_permission_id} still exists in the database, unable to delete permission")

    def test_data_validation(self):
        grant_admin_status()

        payload = self.valid_payloads[0]
        parameters = [
            # Parameter name        # Accepted type
            'user_permission_id'    # str -> string formatted int
        ]
        for param_name in parameters:
            ## Set up a temp permission to delete
            set_up_permissions(windows_username=TEST_WINDOWS_USERNAME, categories=[DEFAULT_CATEGORY])
            self.valid_permission_id = str(UserPermissions.objects.using('PerInd').get(
                user__login=TEST_WINDOWS_USERNAME
                ,category__category_name=DEFAULT_CATEGORY
            ).user_permission_id)
            payload['user_permission_id'] = self.valid_permission_id
            if param_name == 'user_permission_id':
                valid   = [str(self.valid_permission_id)]
                invalid = ['a', 5.6, -2.6, '-1', '-1.2', '11.567', '2.2', '4.45', None, False, True, '']
            else:
                raise ValueError(f"test_data_validation(): parameter test not implemented: '{param_name}'. Please remove or implement it")

            for data in valid:
                self.assert_request_param_good(valid_payload=payload, testing_param_name=param_name, testing_data=data)

            for data in invalid:
                self.assert_request_param_bad(valid_payload=payload, testing_param_name=param_name, testing_data=data)
