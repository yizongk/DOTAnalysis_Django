from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, WebGridPageView, PastDueIndicatorsPageView, AdminPanelPageView
urlpatterns = [

    #path('', views.index, name='index'),
    #path('about', views.about, name='about'),
    #path('contact', views.contact, name='contact'),

    path('', HomePageView.as_view(), name='perind_home_view'),
    path('about', AboutPageView.as_view(), name='perind_about_view'),
    path('contact', ContactPageView.as_view(), name='perind_contact_view'),
    path('webgrid', WebGridPageView.as_view(), name='perind_webgrid_view'),
    # path('webgrid', views.webgrid_view, name='perind_webgrid_view'),
    path('save_perind_data_api', views.SavePerIndDataApi, name='save_perind_data_api'),
    path('get_csv_cur_ctx_api', views.GetCsvApi, name='get_csv_cur_ctx_api'),
    path('pastdueindicators', PastDueIndicatorsPageView.as_view(), name='perind_pastdueindicators'),
    path('adminpanel', AdminPanelPageView.as_view(), name='perind_adminpanel'),
    path('admin_panel_api_save_permission_data', views.AdminPanelApiSavePermissionData, name='admin_panel_api_save_permission_data'),
    path('admin_panel_api_add_row_permission', views.AdminPanelApiAddRowPermission, name='admin_panel_api_add_row_permission'),
    path('admin_panel_api_delete_row_permission', views.AdminPanelApiDeleteRowPermission, name='admin_panel_api_delete_row_permission'),

]
