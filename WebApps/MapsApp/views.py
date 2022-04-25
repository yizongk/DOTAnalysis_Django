from django.shortcuts import render

from django.views.generic import TemplateView

# Create your views here.

class HomePageView(TemplateView):
    template_name   = 'MapsApp.template.home.html'
    get_success     = True
    get_error         = None

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context["get_success"]  = self.get_success
            context["get_error"]      = self.get_error
            return context
        except Exception as e:
            context["get_success"]  = False
            context["get_error"]      = None
            return context

class AboutPageView(TemplateView):
    template_name   = 'MapsApp.template.about.html'
    get_success     = True
    get_error         = None

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context["get_success"]  = self.get_success
            context["get_error"]      = self.get_error
            return context
        except Exception as e:
            context["get_success"]  = False
            context["get_error"]      = None
            return context

class ContactPageView(TemplateView):
    template_name   = 'MapsApp.template.contact.html'
    get_success     = True
    get_error         = None

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context["get_success"]  = self.get_success
            context["get_error"]      = self.get_error
            return context
        except Exception as e:
            context["get_success"]  = False
            context["get_error"]      = None
            return context

class EquityMap(TemplateView):
    template_name = 'MapsApp.template.equity_map.html'
    get_success     = True
    get_error         = None

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context["get_success"]  = self.get_success
            context["get_error"]      = self.get_error
            return context
        except Exception as e:
            context["get_success"]  = False
            context["get_error"]      = None
            return context