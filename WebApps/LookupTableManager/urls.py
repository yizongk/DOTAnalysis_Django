from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, WorkUnitsView, UpdateWU
urlpatterns = [

    path('', HomePageView.as_view(), name='LookupTableManager_home_view'),
    path('about', AboutPageView.as_view(), name='LookupTableManager_about_view'),
    path('contact', ContactPageView.as_view(), name='LookupTableManager_contact_view'),
    path('work_units/',WorkUnitsView.as_view(), name = 'LookupTableManager_work_units_view'),
    path('update_wu/', views.UpdateWU, name='LookupTableManager_update_wu')
]