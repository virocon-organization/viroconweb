"""
URL settings
"""
from django.conf.urls import include, url
from . import views

app_name = 'info'

urlpatterns = [
    url(r'^imprint$', views.impressum, name='imprint'),
    url(r'^about$', views.about, name='about'),
    url(r'^help$', views.help, name='help'),
]
