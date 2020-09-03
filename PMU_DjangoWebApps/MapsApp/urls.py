from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, Map1
urlpatterns = [
    path('', HomePageView.as_view(), name='mapsapp_home_view'),
    path('about', AboutPageView.as_view(), name='mapsapp_about_view'),
    path('contact', ContactPageView.as_view(), name='mapsapp_contact_view'),
    path('map1', Map1.as_view(), name='mapsapp_map1_view'),
]
