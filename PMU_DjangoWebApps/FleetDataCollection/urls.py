from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, DriverAndTypeAssignmentConfirmationPageView
urlpatterns = [

    path('', HomePageView.as_view(), name='fleetdatacollection_home_view'),
    path('about', AboutPageView.as_view(), name='fleetdatacollection_about_view'),
    path('contact', ContactPageView.as_view(), name='fleetdatacollection_contact_view'),
    path('driverandtypeconfirmation', DriverAndTypeAssignmentConfirmationPageView.as_view(), name='fleetdatacollection_driverandtypeconfirmation_view'),

]