from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, LookUpView
urlpatterns = [

    path('', HomePageView.as_view(), name='LookupTableManager_home_view'),
    path('about', AboutPageView.as_view(), name='LookupTableManager_about_view'),
    path('contact', ContactPageView.as_view(), name='LookupTableManager_contact_view'),
    path('table/',LookUpView.as_view(), name = 'LookupTableManager_table_view'),

]