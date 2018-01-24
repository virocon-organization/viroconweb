from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core import validators


class User(AbstractUser):
    """
    This class inherits form AbstractUser and represents the user.

    Attributes
    ----------
    TYPES : possible choices for type_of_use.
    username : unique user name.
    first_name : first name of a user.
    last_name : last name of a user.
    email : the email address of a user.
    organisation : the organisation (e.g. company or university name) of the user.
    type_of_use : for which purpose the user uses ViroCon.

    """
    TYPES = (('academic', 'academic'), ('commercial', 'commercial'))
    username = models.CharField('user name', max_length=30, unique=True,
                                help_text=('Required. 30 characters or fewer. Letters, digits and '
                                           '@/./+/-/_ only.'),
                                validators=[validators.RegexValidator(r'^[\w.@+-]+$',
                                                                      ('Enter a valid username. '
                                                                       'This value may contain only letters, numbers '
                                                                       'and @/./+/-/_ characters.'), 'invalid'), ],
                                error_messages={
                                    'unique': "A user with that username already exists.",
                                })
    first_name = models.CharField('first name', max_length=30)
    last_name = models.CharField('last name', max_length=30)
    email = models.EmailField(unique=True,
                              blank=True,
                              error_messages={
                                  'unique': "A user with that email already exists."})
    organisation = models.CharField(max_length=100)
    type_of_use = models.CharField(choices=TYPES, max_length=11)