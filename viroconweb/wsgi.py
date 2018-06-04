"""
WSGI config for ViroCon.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viroconweb.settings")

# Redirect from the heroku domain to the custom domain. This code block is
# based on: https://stackoverflow.com/questions/2285879/how-do-i-redirect-
# domain-com-to-www-domain-com-under-django
_application = get_wsgi_application()
_application = DjangoWhiteNoise(_application)
def application(environ, start_response):
    if '.herokuapp.com' in environ['HTTP_HOST']:
        start_response('301 Redirect',
                       [('Location', 'http://www.viroconweb.com/'),])
        return []
    return _application(environ, start_response)
