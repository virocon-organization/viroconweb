from django.contrib.auth import models
from django.db import models

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    TYPES = (('academic', 'academic'), ('commercial', 'commercial'), ('other', 'other'))
    email = models.EmailField(unique=True,
                              blank=True,
                              error_messages={
                                  'unique': "A user with that email already exists."})
    organisation = models.CharField(max_length=100)
    type_of_use = models.CharField(choices=TYPES, max_length=11)
