from django.shortcuts import render

from django.views.generic import TemplateView

# Create your views here.

class HomePageView(TemplateView):
    template_name   = 'MapsApp.template.home.html'
    req_success     = True
    err_msg         = None

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context["req_success"]  = self.req_success
            context["err_msg"]      = self.err_msg
            return context
        except Exception as e:
            context["req_success"]  = False
            context["err_msg"]      = None
            return context

class AboutPageView(TemplateView):
    template_name   = 'MapsApp.template.about.html'
    req_success     = True
    err_msg         = None

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context["req_success"]  = self.req_success
            context["err_msg"]      = self.err_msg
            return context
        except Exception as e:
            context["req_success"]  = False
            context["err_msg"]      = None
            return context

class ContactPageView(TemplateView):
    template_name   = 'MapsApp.template.contact.html'
    req_success     = True
    err_msg         = None

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context["req_success"]  = self.req_success
            context["err_msg"]      = self.err_msg
            return context
        except Exception as e:
            context["req_success"]  = False
            context["err_msg"]      = None
            return context

class EquityMap(TemplateView):
    template_name = 'MapsApp.template.equity_map.html'
    req_success     = True
    err_msg         = None

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context["req_success"]  = self.req_success
            context["err_msg"]      = self.err_msg
            return context
        except Exception as e:
            context["req_success"]  = False
            context["err_msg"]      = None
            return context