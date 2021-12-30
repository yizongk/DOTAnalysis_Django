from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, WebGridPageView, PastDueIndicatorsPageView, AdminPanelPageView, UserPermissionsPanelPageView, UsersPanelPageView
urlpatterns = [

    #path('', views.index, name='index'),
    #path('about', views.about, name='about'),
    #path('contact', views.contact, name='contact'),

    path('', HomePageView.as_view(), name='perind_home_view'),
    path('about', AboutPageView.as_view(), name='perind_about_view'),
    path('contact', ContactPageView.as_view(), name='perind_contact_view'),
    path('webgrid', WebGridPageView.as_view(), name='perind_webgrid_view'),
    # path('webgrid', views.webgrid_view, name='perind_webgrid_view'),
    path('perind_update_data_api', views.PerIndApiUpdateData, name='perind_update_data_api'),
    path('get_csv_cur_ctx_api', views.PerIndApiGetCsv, name='get_csv_cur_ctx_api'),
    path('pastdueindicators', PastDueIndicatorsPageView.as_view(), name='perind_pastdueindicators'),
    path('adminpanel', AdminPanelPageView.as_view(), name='perind_adminpanel'),
    path('userpermissionspanel', UserPermissionsPanelPageView.as_view(), name='perind_userpermissionspanel'),
    path('user_permissions_panel_api_update_data', views.UserPermissionsPanelApiUpdateData, name='user_permissions_panel_api_update_data'),
    path('user_permissions_panel_api_add_row', views.UserPermissionsPanelApiAddRow, name='user_permissions_panel_api_add_row'),
    path('user_permissions_panel_api_delete_row', views.UserPermissionsPanelApiDeleteRow, name='user_permissions_panel_api_delete_row'),
    path('userspanel', UsersPanelPageView.as_view(), name='perind_userspanel'),
    path('users_panel_api_add_row', views.UsersPanelApiAddRow, name='users_panel_api_add_row'),
    path('users_panel_api_delete_row', views.UsersPanelApiDeleteRow, name='users_panel_api_delete_row'),
    path('users_panel_api_update_row', views.UsersPanelApiUpdateData, name='users_panel_api_update_row'),

]
