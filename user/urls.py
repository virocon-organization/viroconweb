from django.conf.urls import url
from . import views

app_name = 'user'

urlpatterns = [
    url(r'^create/$', views.create, name='create'),

    url(r'^authentication/$', views.authentication, name='authentication'),

    url(r'^logout/$', views.logout, name='logout'),

    url(r'^profile/$', views.profile, name='profile'),

    url(r'^edit/$', views.edit, name='edit'),

    url(r'^change-password/$', views.change_password, name='change-password'),
]
