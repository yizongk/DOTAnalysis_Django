from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, DataCollectionPageView, DataGridPageView, UpdatePotholesData
urlpatterns = [

    path('', HomePageView.as_view(), name='dailypothole_home_view'),
    path('about', AboutPageView.as_view(), name='dailypothole_about_view'),
    path('contact', ContactPageView.as_view(), name='dailypothole_contact_view'),
    path('data_collection', DataCollectionPageView.as_view(), name='dailypothole_data_collection_view'),
    path('data_grid', DataGridPageView.as_view(), name='dailypothole_data_grid_view'),
    path('update_potholes_data', views.UpdatePotholesData, name='dailypothole_update_potholes_data_api'),

]