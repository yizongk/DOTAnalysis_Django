from django.urls import path
from . import views
from .views import HomePageView, AboutPageView, ContactPageView, DataCollectionPageView, DataGridPageView, ComplaintsInputPageView, ReportsPageView, UpdatePotholesData, UpdateComplaintsData, LookupComplaintsData, GetPDFReport
urlpatterns = [

    path('', HomePageView.as_view(), name='dailypothole_home_view'),
    path('about', AboutPageView.as_view(), name='dailypothole_about_view'),
    path('contact', ContactPageView.as_view(), name='dailypothole_contact_view'),
    path('data_collection', DataCollectionPageView.as_view(), name='dailypothole_data_collection_view'),
    path('data_grid', DataGridPageView.as_view(), name='dailypothole_data_grid_view'),
    path('complaints_input', ComplaintsInputPageView.as_view(), name='dailypothole_complaints_input_view'),
    path('reports', ReportsPageView.as_view(), name='dailypothole_reports_view'),
    path('update_potholes_data', views.UpdatePotholesData, name='dailypothole_update_potholes_data_api'),
    path('update_complaints_data', views.UpdateComplaintsData, name='dailypothole_update_complaints_data_api'),
    path('lookup_complaints_data', views.LookupComplaintsData, name='dailypothole_lookup_complaints_data_api'),
    path('get_pdf_report', views.GetPDFReport, name='dailypothole_get_pdf_report_api'),

]