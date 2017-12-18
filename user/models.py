from django.db import models

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    The class inherits form AbstractUser and represents the user.

    Attributes
    ----------
    TYPES : possible choices for type_of_use.
    email : the email address of a user.
    organisation : the organisation (company) of the user.
    type_of_use : for which purpose the user uses ViroCon.

    """
    TYPES = (('academic', 'academic'), ('commercial', 'commercial'), ('other', 'other'))
    email = models.EmailField(unique=True,
                              blank=True,
                              error_messages={
                                  'unique': "A user with that email already exists."})
    organisation = models.CharField(max_length=100)
    type_of_use = models.CharField(choices=TYPES, max_length=11)
