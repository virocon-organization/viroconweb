"""
Url design for the user app.

Attributes
----------
app_name : str
    sets the app name to call it e.g. in templates.

urlpatterns : list of url's
    stores the url design of the user app.

"""
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

    # reset password url's
    url(r'^password_reset/$', views.ResetView.as_view(), name='password_reset'),

    url(r'^password_reset/done/$', views.ResetDoneView.as_view(), name='password_reset_done'),

    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.ResetConfirmView.as_view(), name='password_reset_confirm'),

    url(r'^reset/done$', views.ResetCompleteView.as_view(), name='password_reset_complete'),

]
