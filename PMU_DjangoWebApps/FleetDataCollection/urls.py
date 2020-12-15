from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, DriverAndTypeAssignmentConfirmationPageView, GetPermittedEmpDataList, UpdateM5DriverVehicleDataConfirmations, GetM5LookUpDataList, GetEmpLookUpDataList, AdminPanelPageView, WuPermissionsPanelPageView
urlpatterns = [

    path('', HomePageView.as_view(), name='fleetdatacollection_home_view'),
    path('about', AboutPageView.as_view(), name='fleetdatacollection_about_view'),
    path('contact', ContactPageView.as_view(), name='fleetdatacollection_contact_view'),
    path('driver_and_type_confirmation', DriverAndTypeAssignmentConfirmationPageView.as_view(), name='fleetdatacollection_driver_and_type_confirmation_view'),
    path('get_permitted_pms_list', views.GetPermittedEmpDataList, name='fleetdatacollection_get_permitted_pms_list'),
    path('update_m5_driver_vehicle_data_confirmations', views.UpdateM5DriverVehicleDataConfirmations, name='fleetdatacollection_update_m5_driver_vehicle_data_confirmations'),
    path('get_m5_list', views.GetM5LookUpDataList, name='fleetdatacollection_get_m5_list'),
    path('get_pms_list', views.GetEmpLookUpDataList, name='fleetdatacollection_get_pms_list'),
    path('adminpanel', AdminPanelPageView.as_view(), name='fleetdatacollection_adminpanel_view'),
    path('wupermissionspanel', WuPermissionsPanelPageView.as_view(), name='fleetdatacollection_wupermissionspanel_view'),

]