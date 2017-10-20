from django.conf.urls import url
from . import views
from django.contrib.auth.views import (
    password_reset,
    password_reset_done,
    password_reset_confirm,
    password_reset_complete
)

app_name = 'user'

urlpatterns = [
    url(r'^registration/$', views.register_user, name='register'),

    url(r'^login/$', views.login, name='user'),

    url(r'^logout/$', views.logout, name='logout'),

    url(r'^profile/$', views.profile, name='profile'),

    url(r'^profile/edit/$', views.edit_profile, name='edit_profile'),

    url(r'^profile/password/$', views.change_password, name='change_password'),

    url(r'^reset_password/$', password_reset,
        {'template_name': 'user/reset_password.html', 'post_reset_redirect': 'user:password_reset_done',
         'email_template_name': 'user/reset_password_email.html'}, name='reset_password'),

    url(r'^reset_password/done/$', password_reset_done, {'template_name': 'user/reset_password_done.html'},
        name='password_reset_done'),

    url(r'^reset_password/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', password_reset_confirm,
        {'template_name': 'user/reset_password_confirm.html',
         'post_reset_redirect': 'user:password_reset_complete'}, name='password_reset_confirm'),

    url(r'^reset_password/complete/$', password_reset_complete,
        {'template_name': 'user/reset_password_complete.html'}, name='password_reset_complete')
]
