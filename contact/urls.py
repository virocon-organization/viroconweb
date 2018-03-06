"""URL settings
"""
from django.conf.urls import include, url
from . import views

app_name = 'contact'

urlpatterns = [
    url(r'^impressum$', views.impressum, name='impressum'),
    url(r'^about$', views.about, name='about'),
    url(r'^help$', views.help, name='help'),
]
