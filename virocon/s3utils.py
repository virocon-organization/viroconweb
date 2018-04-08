"""
Custom S3 storage backends to store files in subfolders.

This file was created based on the description from:
http://martinbrochhaus.com/s3.html
and https://stackoverflow.com/questions/14266950/wrong-url-with-django-
sorl-thumbnail-with-amazon-s3
"""
from storages.backends.s3boto import S3BotoStorage


class MediaRootS3BotoStorage(S3BotoStorage):
    location = 'media'
