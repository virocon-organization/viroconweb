from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """This class represents a form to create a new user.
    """
    class Meta(UserCreationForm.Meta):
        """metadata for the model User. Selects fields of the moodel.
        """
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name', 'organisation', 'type_of_use',)


class CustomUserChangeForm(UserChangeForm):
    """This class represents a form to change attributes of a user. The Form is used in the admin area.
    """
    class Meta(UserChangeForm.Meta):
        """metadata for the model User. Selects fields of the model.
        """
        model = User
        fields = '__all__'


class CustomUserEditForm(UserChangeForm):
    """This class represents a form to change attributes of a user by himself.

    Attributes
    ----------
    password : str
        None
    """
    password = None

    class Meta(UserChangeForm.Meta):
        """metadata for the model User. Selects fields of the model.
        """
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'organisation', 'type_of_use')


class CustomUserAdmin(UserAdmin):
    """This class provides which fields are seen in the admin area.

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
