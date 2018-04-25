"""
All user forms that are used to edit or generate a user.
"""
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """
    A form to create a new user.
    """
    class Meta(UserCreationForm.Meta):
        """
        Metadata for the model User. Defines which fields should be editable in this form.
        """
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name', 'organisation', 'type_of_use',)


class CustomUserChangeForm(UserChangeForm):
    """
    A form to change attributes of a user. This form is only used in the admin area.
    """
    class Meta(UserChangeForm.Meta):
        """
        Metadata for the model User. Defines which fields should be editable in this form.
        """
        model = User
        fields = '__all__'


class CustomUserEditForm(UserChangeForm):
    """
    A form to change attributes of a user by herself/himself.

    Attributes
    ----------
    password : str
       It is not possible to change the user password in this form. The password value is equal to None so
       the encoded password is not visible in the template. Otherwise it will be possible to see the encoded password
       in the template.
    """
    password = None

    class Meta(UserChangeForm.Meta):
        """
        Metadata for the model User. Defines which fields should be editable in this form.
        """
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'organisation', 'type_of_use')


class CustomUserAdmin(UserAdmin):
    """
    Defines which fields are seen in the admin area.

    Attributes
    ---------
    form : CustomUserChangeForm
        exchange UserChangeForm to CustomUserChangeForm
    fieldsets : list of fields of the user model.
        editable fields.
    """
    form = CustomUserChangeForm

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('organisation', 'type_of_use',)}),)
