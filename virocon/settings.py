"""
Django settings for ViroCon.

Generated by 'django-admin startproject' using Django 1.10.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
import dj_database_url
import random
import string

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The following lines of codes are based on the description from:
# http://martinbrochhaus.com/s3.html
USE_S3 = True
key_exists = "AWS_ACCESS_KEY_ID" in os.environ
if not key_exists:
    print('Warning: AWS_ACCESS_KEY_ID is not set. Setting it to XXX')
    AWS_ACCESS_KEY_ID = 'XXX'
else:
    AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
key_exists = "AWS_SECRET_ACCESS_KEY" in os.environ
if not key_exists:
    print('Warning: AWS_SECRET_ACCESS_KEY is not set. Setting it to XXX')
    AWS_SECRET_ACCESS_KEY = 'XXX'
else:
    AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
AWS_STORAGE_BUCKET_NAME = 'virocon-media-dev'
AWS_QUERYSTRING_AUTH = False
S3_URL = 'https://s3.eu-central-1.amazonaws.com/%s' % AWS_STORAGE_BUCKET_NAME

if USE_S3:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    THUMBNAIL_DEFAULT_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = S3_URL + '/media/'
    # Needed for S3 Frankfurt, see https://github.com/boto/boto/issues/2916
    os.environ['S3_USE_SIGV4'] = 'True'
else:
    MEDIA_URL = '/contour/media/user_generated/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'contour/media/user_generated')


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
# The following lines are needed to handle static files properly (i.e. CSS, Java
# Script, Images)
# In django media files are NOT static files. Media files are files uploaded by
# the user, in ViroCon for example the .csv files, images generated by fits
# and the latex report.
# For more information on the static fiels handling, take a look at:
# from: https://devcenter.heroku.com/articles/
# The following 4 lines are from:
# https://devcenter.heroku.com/articles/django-assets
STATIC_ROOT = os.path.join(BASE_DIR, 'collectedstatics')
STATIC_URL = '/static/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)
STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'


# SECURITY WARNING: keep the secret key used in production secret!
key_exists = "SECRET_KEY" in os.environ
if not key_exists:
    print('Warning: SECRET_KEY is not set. For test purposes I am setting '
          'it to a random hash')
    SECRET_KEY = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=10))
else:
    SECRET_KEY = os.environ["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# select own user model
AUTH_USER_MODEL = 'user.User'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    # Disable Django's own staticfiles handling in favour of WhiteNoise, for
    # greater consistency between gunicorn and `./manage.py runserver`. See:
    # http://whitenoise.evans.io/en/stable/django.html#using-whitenoise-in-development
    #'whitenoise.runserver_nostatic',
    #'django.contrib.staticfiles',
    'latexify',
    'django.contrib.staticfiles', # a requirement for latexify
    'storages',
    'contour.apps.ContourConfig',
    'user.apps.UserConfig',
    'info.apps.InfoConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'virocon.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ["./templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'virocon.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    './static/',
]

ALLOWED_HOSTS = [
    '192.168.2.8',
    '0.0.0.0',
    '192.168.178.89',
    '127.0.0.1',
    'localhost',
    '134.102.113.71.',
    '134.102.162.102',
    '134.102.162.29',
    '134.102.174.219',
    'serene-sierra-98066.herokuapp.com'
]

# execute this for debug smtp:
# python -m smtpd -n -c DebuggingServer localhost:1025

# un-comment this for debug smtp:
# EMAIL_HOST = 'localhost'
# EMAIL_PORT = 1025

# comment out this if debug smtp should be executed:
# DEFAULT_FROM_EMAIL = ''

EMAIL_HOST = 'smtp.uni-bremen.de'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'virocon@uni-bremen.de'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'no-reply@virocon.de'
key_exists = "EMAIL_HOST_PASSWORD" in os.environ
if not key_exists:
    print('Warning: EMAIL_HOST_PASSWORD is not set')
else:
    EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"]


# see https://devcenter.heroku.com/articles/django-app-configuration
# Change 'default' database configuration with $DATABASE_URL.
db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# see https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/
#CSRF_COOKIE_SECURE = True
#SESSION_COOKIE_SECURE = True