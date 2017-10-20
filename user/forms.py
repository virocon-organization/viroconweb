from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm


class LoginForm(AuthenticationForm):
    pass


# Represents the form of the user class
class RegistrationForm(UserCreationForm):
    # Adds a field for the user-email-address
    email = forms.EmailField(required=True)

    # Extends the password confirmation field of the UserCreationForm-class
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput,
        strip=False,
    )

    username = forms.CharField(required=True)

    # Summarizes the fields of the User class to a model
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    # extends the save method of the UserCreationForm class and adds the defined fields
    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.username = self.cleaned_data['username']

        if commit:
            user.save()

        return user


# Class defines the clean GUI-view at user/profile/edit
class EditProfileForm(UserChangeForm):
    # the "no-raw-password-message" isn't shown anymore
    password = None

    # defines fields to be shown to the user to change
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")
