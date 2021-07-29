from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, PotholeDataEntryPageView, PotholeDataGridPageView, ComplaintsInputPageView, ReportsPageView, AdminPanelPageView, UsersPanelPageView, UserPermissionsPanelPageView
urlpatterns = [

    path('', HomePageView.as_view(), name='dailypothole_home_view'),
    path('about', AboutPageView.as_view(), name='dailypothole_about_view'),
    path('contact', ContactPageView.as_view(), name='dailypothole_contact_view'),
    path('pothole_data_entry', PotholeDataEntryPageView.as_view(), name='dailypothole_pothole_data_entry_view'),
    path('pothole_data_grid', PotholeDataGridPageView.as_view(), name='dailypothole_pothole_data_grid_view'),
    path('complaints_input', ComplaintsInputPageView.as_view(), name='dailypothole_complaints_input_view'),
    path('reports', ReportsPageView.as_view(), name='dailypothole_reports_view'),
    path('update_potholes_data', views.UpdatePotholesData, name='dailypothole_update_potholes_data_api'),
    path('update_complaints_data', views.UpdateComplaintsData, name='dailypothole_update_complaints_data_api'),
    path('lookup_complaints_data', views.LookupComplaintsData, name='dailypothole_lookup_complaints_data_api'),
    path('get_pdf_report', views.GetPDFReport, name='dailypothole_get_pdf_report_api'),
    path('lookup_potholes_and_crew_data', views.LookupPotholesAndCrewData, name='dailypothole_lookup_potholes_and_crew_data_api'),
    path('admin_panel', AdminPanelPageView.as_view(), name='dailypothole_admin_panel_view'),
    path('users_panel', UsersPanelPageView.as_view(), name='dailypothole_users_panel_view'),
    path('add_user', views.AddUser, name='dailypothole_add_user_api'),
    path('update_user', views.UpdateUser, name='dailypothole_update_user_api'),
    path('delete_user', views.DeleteUser, name='dailypothole_delete_user_api'),
    path('user_permissions_panel', UserPermissionsPanelPageView.as_view(), name='dailypothole_user_permissions_panel_view'),
    path('add_user_permission', views.AddUserPermission, name='dailypothole_add_user_permission_api'),
    path('update_user_permission', views.UpdateUserPermission, name='dailypothole_update_user_permission_api'),
    path('delete_user_permission', views.DeleteUserPermission, name='dailypothole_delete_user_permission_api'),

]