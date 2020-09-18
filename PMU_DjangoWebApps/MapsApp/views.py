from django.shortcuts import render

from django.views.generic import TemplateView

# Create your views here.

class HomePageView(TemplateView):
    template_name = 'MapsApp.template.home.html'

class AboutPageView(TemplateView):
    template_name = 'MapsApp.template.about.html'

class ContactPageView(TemplateView):
    template_name = 'MapsApp.template.contact.html'

class EquityMap(TemplateView):
    template_name = 'MapsApp.template.equity_map.html'