from django.conf.urls import url
from . import views

# For URLs we use the convention described here: https://stackoverflow.com/
# questions/31816624/naming-convention-for-django-url-templates-models-and-views
# For the URL names we treat them as variables and consequently use underscore
# as described in PEP8

app_name = 'enviro'

urlpatterns = [

    # URL to download the latex-based pdf report
    url(r'^download_pdf$', views.download_pdf, name='download_pdf'),

    # --------------------------------------------------------------------------
    # EnvironmentalContour
    url(r'^contours/(?P<pk>[0-9]+)/$',
        views.EnvironmentalContourHandler.show,
        name='environmental_contour_show'),

    url(r'^contours/(?P<pk>[0-9]+)/delete/$',
        views.EnvironmentalContourHandler.delete,
        name='environmental_contour_delete'),

    url(r'^contours/overview$',
        views.EnvironmentalContourHandler.overview,
        name='environmental_contour_overview'),

    # --------------------------------------------------------------------------
    # ProbabilisticModel
    url(r'^models/add/([0-9]{2})/$',
        views.ProbabilisticModelHandler.add,
        name='probabilistic_model_add'),

    url(r'^models/overview$',
        views.ProbabilisticModelHandler.overview,
        name='probabilistic_model_overview'),

    url(r'^models/(?P<pk>[0-9]+)/update/$',
        views.ProbabilisticModelHandler.update,
        name='probabilistic_model_update'),

    url(r'^models/(?P<pk>[0-9]+)/delete/$',
        views.ProbabilisticModelHandler.delete,
        name='probabilistic_model_delete'),

    url(r'models/select/$',
        views.ProbabilisticModelHandler.select,
        name='probabilistic_model_select'),

    url(r'^models/(?P<pk>[0-9]+)/(?P<method>[IH])/calc/$',
        views.ProbabilisticModelHandler.calculate,
        name='probabilistic_model_calc'),

    url(r'^models/number-of-variables/$',
        views.ProbabilisticModelHandler.set_variables_number,
        name='set_probabilistic_model_number'),

    url(r'^models/(?P<pk>[0-9]+)/$',
        views.ProbabilisticModelHandler.show_model,
        name='probabilistic_model_show'),

    # --------------------------------------------------------------------------
    # MeasureFileModel
    url(r'measurefiles/add/',
        views.MeasureFileHandler.add,
        name='measure_file_model_add'),

    url(r'measurefiles/overview/$',
        views.MeasureFileHandler.overview,
        name='measure_file_model_overview'),

    url(r'^measurefiles/(?P<pk>[0-9]+)/update/$',
        views.MeasureFileHandler.update,
        name='measure_file_model_update'),

    url(r'^measurefiles/(?P<pk>[0-9]+)/delete/$',
        views.MeasureFileHandler.delete,
        name='measure_file_model_delete'),

    url(r'^measurefiles/select$',
        views.MeasureFileHandler.select,
        name='measure_file_model_select'),

    url(r'^measurefiles/(?P<pk>[0-9]+)/fit$',
        views.MeasureFileHandler.fit_file,
        name='measure_file_model_fit'),

    url(r'^measurefiles/(?P<pk>[0-9]+)/new/fit$',
        views.MeasureFileHandler.new_fit,
        name='measure_file_model_new_fit'),

    url(r'^measurefiles/(?P<pk>[0-9]+)/plot$',
        views.MeasureFileHandler.plot_file,
        name='measure_file_model_plot'),
]
