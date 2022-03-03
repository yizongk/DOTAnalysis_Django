from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, EmpGridPageView, OrgChartPageView
urlpatterns = [
    path('', HomePageView.as_view(), name='orgchartportal_home_view'),
    path('about', AboutPageView.as_view(), name='orgchartportal_about_view'),
    path('contact', ContactPageView.as_view(), name='orgchartportal_contact_view'),
    path('empgrid', EmpGridPageView.as_view(), name='orgchartportal_empgrid_view'),
    path('orgchart', OrgChartPageView.as_view(), name='orgchartportal_orgchart_view'),
    path('get_client_wu_permissions_list', views.GetClientWUPermissions, name='orgchartportal_get_client_wu_permissions_list'),
    path('get_client_teammates_list', views.GetClientTeammates, name='orgchartportal_get_client_teammates_list'),
    path('get_emp_grid_stats', views.GetEmpGridStats, name='orgchartportal_get_emp_grid_stats'),
    path('org_chart_get_emp_csv', views.OrgChartGetEmpCsv, name='orgchartportal_org_chart_get_emp_csv'),
    path('get_commissioner_pms', views.GetCommissionerPMS, name='orgchartportal_get_commissioner_pms'),
    path('update_employee_data', views.UpdateEmployeeData, name='orgchartportal_update_employee_data'),
]
