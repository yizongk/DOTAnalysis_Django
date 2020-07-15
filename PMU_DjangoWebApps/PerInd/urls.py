from django.urls import path

from . import views
from .views import HomePageView, AboutPageView, ContactPageView
urlpatterns = [
    
    #path('', views.index, name='index'),
    #path('about', views.about, name='about'),
    #path('contact', views.contact, name='contact'),
    
    path('webgrid', views.webgrid, name='webgrid'),
     path('', HomePageView.as_view(), name='home'),
    path('about/', AboutPageView.as_view(), name='about'),
    path('contact/', ContactPageView.as_view(), name='contact'),

]
