from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.admin import UserAdmin
from .models import User

# Represents the form of the user class
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    """
    The class represents a form the create a new user.
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name', 'organisation', 'type_of_use',)


class CustomUserChangeForm(UserChangeForm):
    """
    The class represents a form to change attributes of a user. The Form is used in the admin area.
    """
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'


class CustomUserEditForm(UserChangeForm):
    """
    The class represents a form to change attributes of a user by himself.
    """
    password = None

    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'organisation', 'type_of_use')


class CustomUserAdmin(UserAdmin):
    """
    The class provides which fields are seen in the admin area.
    """
    form = CustomUserChangeForm

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('organisation', 'type_of_use',)}),)
