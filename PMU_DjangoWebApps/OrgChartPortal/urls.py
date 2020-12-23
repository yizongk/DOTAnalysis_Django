from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, EmpGridPageView
urlpatterns = [
    path('', HomePageView.as_view(), name='orgchartportal_home_view'),
    path('about', AboutPageView.as_view(), name='orgchartportal_about_view'),
    path('contact', ContactPageView.as_view(), name='orgchartportal_contact_view'),
    path('empgrid', EmpGridPageView.as_view(), name='orgchartportal_empgrid_view'),
]
