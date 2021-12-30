from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, EquityMap
urlpatterns = [
    path('', HomePageView.as_view(), name='mapsapp_home_view'),
    path('about', AboutPageView.as_view(), name='mapsapp_about_view'),
    path('contact', ContactPageView.as_view(), name='mapsapp_contact_view'),
    path('equity_map', EquityMap.as_view(), name='mapsapp_equity_map_view'),
]
