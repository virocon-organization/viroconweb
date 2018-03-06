"""URL settings.

Attributes
---------
app_name : str
    name of the app e.g. to call it in templates.
"""
from django.conf.urls import include, url
from . import views

app_name = 'home'

urlpatterns = [
    url(r'^$', views.home, name='home'),
]
