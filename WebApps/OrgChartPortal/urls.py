from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, EmpGridPageView, OrgChartPageView, AdminPanelPageView, ManageUsersPageView, ManagePermissionsPageView, HowToUsePageView
urlpatterns = [
    path('', HomePageView.as_view(), name='orgchartportal_home_view'),
    path('about', AboutPageView.as_view(), name='orgchartportal_about_view'),
    path('contact', ContactPageView.as_view(), name='orgchartportal_contact_view'),
    path('empgrid', EmpGridPageView.as_view(), name='orgchartportal_empgrid_view'),
    path('orgchart', OrgChartPageView.as_view(), name='orgchartportal_orgchart_view'),
    path('admin_panel', AdminPanelPageView.as_view(), name='orgchartportal_admin_panel_view'),
    path('manage_users', ManageUsersPageView.as_view(), name='orgchartportal_manage_users_view'),
    path('manage_permissions', ManagePermissionsPageView.as_view(), name='orgchartportal_manage_permissions_view'),
    path('get_client_wu_permissions_list', views.GetClientWUPermissions, name='orgchartportal_get_client_wu_permissions_list'),
    path('get_client_teammates_list', views.GetClientTeammates, name='orgchartportal_get_client_teammates_list'),
    path('emp_grid_get_csv_export', views.EmpGridGetCsvExport, name='orgchartportal_emp_grid_get_csv_export'),
    path('get_emp_grid_stats', views.GetEmpGridStats, name='orgchartportal_get_emp_grid_stats'),
    path('org_chart_get_emp_csv', views.OrgChartGetEmpCsv, name='orgchartportal_org_chart_get_emp_csv'),
    path('get_commissioner_pms', views.GetCommissionerPMS, name='orgchartportal_get_commissioner_pms'),
    path('update_employee_data', views.UpdateEmployeeData, name='orgchartportal_update_employee_data'),
    path('add_user', views.AddUser, name='orgchartportal_add_user'),
    path('delete_user', views.DeleteUser, name='orgchartportal_delete_user'),
    path('update_user', views.UpdateUser, name='orgchartportal_update_user'),
    path('add_user_permission', views.AddUserPermission, name='orgchartportal_add_user_permission'),
    path('delete_user_permission', views.DeleteUserPermission, name='orgchartportal_delete_user_permission'),
    path('how_to_use', HowToUsePageView.as_view(), name='orgchartportal_how_to_use_view'),
]
