from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, ManageWebAppsPageView
urlpatterns = [
    path('', HomePageView.as_view(), name='UserManagement_home_view'),
    path('about', AboutPageView.as_view(), name='UserManagement_about_view'),
    path('contact', ContactPageView.as_view(), name='UserManagement_contact_view'),
    path('manage_web_apps', ManageWebAppsPageView.as_view(), name='UserManagement_manage_web_apps_view'),
]
