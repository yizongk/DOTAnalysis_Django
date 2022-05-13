from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, ManageWebAppsPageView
urlpatterns = [
    path('', HomePageView.as_view(), name='usermanagement_home_view'),
    path('about', AboutPageView.as_view(), name='usermanagement_about_view'),
    path('contact', ContactPageView.as_view(), name='usermanagement_contact_view'),
    path('manage_web_apps', ManageWebAppsPageView.as_view(), name='usermanagement_manage_web_apps_view'),
]
