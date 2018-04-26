"""
All user forms that are used to edit or generate a user.
"""
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
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


# Thanks to: https://stackoverflow.com/questions/27734185/inform-user-that-
# email-is-invalid-using-djangos-password-reset
class EmailValidationOnForgotPassword(PasswordResetForm):
    """
    Informs the user if he/she tried to reset the password with an email address
    that does not exist.
    """
    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise ValidationError("There is no user registered with the "
                                  "specified email address.")

        return email