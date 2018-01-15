from django.conf.urls import url
from django.contrib.auth import views as auth_views
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

    url(r'^password_reset_done/$', views.ResetDoneView.as_view(), name='password_reset_done'),

    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.ResetConfirmView.as_view(), name='password_reset_confirm'),

    url(r'^password_reset_complete/$', views.ResetCompleteView.as_view(), name='password_reset_complete'),

    # es muss die set password methode gesetzt werden

]
