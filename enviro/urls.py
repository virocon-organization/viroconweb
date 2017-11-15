from django.conf.urls import url
from . import views

# Name der App einfachere URL-Referencen im HTML Code wie z.B. {% url 'enviro:ifrom' %}
app_name = 'enviro'

urlpatterns = [

    # URL to reach the plot_pdf
    url(r'^download_pdf$', views.download_pdf, name='download_pdf'),


    # ------------------------------------------------------------------------------------------------------------------
    # Process Probabilistic Model

    url(r'^probabilistic_model/add/([0-9]{2})/$', views.ProbabilisticModelHandler.add, name='probabilistic_model-add'),

    url(r'^probabilistic_modeloverview$', views.ProbabilisticModelHandler.overview,
        name='probabilistic_model-overview'),

    url(r'^probabilistic_model/(?P<pk>[0-9]+)/update/$', views.ProbabilisticModelHandler.update,
        name='probabilistic_model-update'),

    url(r'^probabilistic_model/(?P<pk>[0-9]+)/delete/$', views.ProbabilisticModelHandler.delete,
        name='probabilistic_model-delete'),

    url(r'probabilistic_model/select/$', views.ProbabilisticModelHandler.select, name='probabilistic_model-select'),

    url(r'^probabilistic_model/(?P<pk>[0-9]+)/(?P<method>[IH])/calc/$', views.ProbabilisticModelHandler.calculate,
        name='probabilistic_model-calc'),

    url(r'^probabilistic_model/set_variables_number/$', views.ProbabilisticModelHandler.set_variables_number,
        name='set-probabilistic_model-number'),

    url(r'^probabilistic_model/(?P<pk>[0-9]+)/plot/$', views.ProbabilisticModelHandler.show_model,
        name='probabilistic_model-show'),

    # ------------------------------------------------------------------------------------------------------------------
    # MeasureFiles

    url(r'measurefiles/add/', views.MeasureFileHandler.add, name='measurefiles-add'),

    url(r'measurefiles/overview/$', views.MeasureFileHandler.overview, name='measurefiles-overview'),

    url(r'^measurefiles/(?P<pk>[0-9]+)/$', views.MeasureFileHandler.update, name='measurefiles-update'),

    url(r'^measurefiles/(?P<pk>[0-9]+)/delete/$', views.MeasureFileHandler.delete, name='measurefiles-delete'),

    url(r'^measurefiles/select$', views.MeasureFileHandler.select, name='measurefiles-select'),

    url(r'^measurefiles/(?P<pk>[0-9]+)/fit$', views.MeasureFileHandler.fit_file, name='measurefiles-fit'),

    url(r'^measurefiles/(?P<pk>[0-9]+)/new/fit$', views.MeasureFileHandler.new_fit, name='measurefiles-new-fit'),

    url(r'^measurefiles/(?P<pk>[0-9]+)/plot$', views.MeasureFileHandler.plot_file, name='measurefiles-plot'),

    # ------------------------------------------------------------------------------------------------------------------
    # Contour

]
