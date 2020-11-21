from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, DriverAndTypeAssignmentConfirmationPageView, GetPermittedPMSList
urlpatterns = [

    path('', HomePageView.as_view(), name='fleetdatacollection_home_view'),
    path('about', AboutPageView.as_view(), name='fleetdatacollection_about_view'),
    path('contact', ContactPageView.as_view(), name='fleetdatacollection_contact_view'),
    path('driver_and_type_confirmation', DriverAndTypeAssignmentConfirmationPageView.as_view(), name='fleetdatacollection_driver_and_type_confirmation_view'),
    path('get_permitted_pms_list', views.GetPermittedPMSList, name='fleetdatacollection_get_permitted_pms_list'),

]