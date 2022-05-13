from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, WorkUnitsView, UpdateWU
urlpatterns = [

    path('', HomePageView.as_view(), name='lookuptablemanager_home_view'),
    path('about', AboutPageView.as_view(), name='lookuptablemanager_about_view'),
    path('contact', ContactPageView.as_view(), name='lookuptablemanager_contact_view'),
    path('work_units/',WorkUnitsView.as_view(), name = 'lookuptablemanager_work_units_view'),
    path('update_wu/', views.UpdateWU, name='lookuptablemanager_update_wu')
]