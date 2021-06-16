from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, DataCollectionPageView
urlpatterns = [

    path('', HomePageView.as_view(), name='dailypothole_home_view'),
    path('about', AboutPageView.as_view(), name='dailypothole_about_view'),
    path('contact', ContactPageView.as_view(), name='dailypothole_contact_view'),
    path('data_collection', DataCollectionPageView.as_view(), name='dailypothole_data_collection_view'),

]