from django.urls import path

from . import views
from .views import HomePageView, AboutPageView, ContactPageView, WebGridPageView
urlpatterns = [
    
    #path('', views.index, name='index'),
    #path('about', views.about, name='about'),
    #path('contact', views.contact, name='contact'),
    
    path('', HomePageView.as_view(), name='home'),
    path('about', AboutPageView.as_view(), name='about'),
    path('contact', ContactPageView.as_view(), name='contact'),
    path('webgrid', WebGridPageView.as_view(), name='webgrid'),

]
