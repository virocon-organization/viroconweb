from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import auth
from django.http import HttpResponseRedirect
from .forms import CustomUserCreationForm
from .forms import CustomUserEditForm
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetCompleteView, PasswordResetConfirmView
import os
import math
from contour.settings import PATH_STATIC, PATH_USER_GENERATED



def authentication(request):
    """This method to login users.

    Parameters
    ----------
    request : to authenticate the user.

    Returns
    -------
    HttpResponse
        if method post and login successful to home. if method post and login unsuccessful to again to login with error
        information. else to login.
    """
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(None, request.POST or None)
        if form.is_valid():
            auth.login(request, form.get_user())
            return HttpResponseRedirect(reverse('contour:index'))
        else:
            return render(request, 'user/login.html', {'form': form})

    else:
        return render(request, 'user/login.html', {'form': form})


# Method is called after userdata is entered and checks database for verification
def authentic(request, username, password):
    """Validates the user login details.
    Parameters
    ----------
    request : request
        to validate user login details.

    username : str
        name for the login.

    password : str
        password for the login.
    """
    user = auth.authenticate(username=username, password=password)
    auth.login(request, user)


def create(request):
    """Creates a new user account .

    Parameters
    ----------
    request : request
        to create a new user account.

    Returns
    -------
    HttpResponse
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            authentic(request, username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            return HttpResponseRedirect('/home')
        else:
            return render(request, 'user/edit.html', {'form': form})
    else:
        return render(request, 'user/edit.html', {'form': CustomUserCreationForm()})


def logout(request):
    """The method logs out a user.

    Parameters
    ---------
    request : request
        to log out.

    Return
    ------
    HttpResponseRedirect
        to home.
    """
    if request.user.is_anonymous:
        return HttpResponseRedirect(reverse('contour:index'))
    else:
        auth.logout(request)
        return HttpResponseRedirect(reverse('contour:index'))


def profile(request):
    """The method views the user profile.

    Parameters
    ----------
    request : request
        to view the user profile.

    Returns
    -------
    HttpResponse
    """
    if request.user.is_anonymous:
        return HttpResponseRedirect(reverse('contour:index'))
    else:
        path = PATH_STATIC + PATH_USER_GENERATED + str(request.user)
        storage_space = user_storage_space(path)
        return render(request,
                      'user/profile.html',
                      {'storage_space': storage_space})


def edit(request):
    """The method allows users to edit their profiles.

    Parameters
    ---------
    request : request
        request to edit a user profile.

    Returns
    -------
    HttpResponse
    """
    if request.user.is_anonymous:
        return HttpResponseRedirect(reverse('contour:index'))
    else:
        if request.method == 'POST':
            form = CustomUserEditForm(request.POST, instance=request.user)

            if form.is_valid():
                form.save()
                return redirect(reverse('user:profile'))
            else:
                return render(request, 'user/edit.html', {'form': form})
        else:
            form = CustomUserEditForm(instance=request.user)
            return render(request, 'user/edit.html', {'form': form})


def change_password(request):
    """
    The method allows a user to change his password.

    Parameters
    ----------
    request : request
        to change the user password

    Returns
    -------
    HttpResponse
    """
    if request.user.is_anonymous:
        return HttpResponseRedirect(reverse('contour:index'))
    else:
        if request.method == 'POST':
            form = PasswordChangeForm(data=request.POST, user=request.user)

            if form.is_valid():
                form.save()
                update_session_auth_hash(request, form.user)
                return redirect(reverse('user:profile'))
            else:
                return render(request, 'user/edit.html', {'form': form})
        else:
            form = PasswordChangeForm(user=request.user)
            return render(request, 'user/edit.html', {'form': form})


class ResetView(PasswordResetView):
    """inherits form PasswordResetView and modifies some attributes.

    Attributes
    ----------
    template_name : str
        defines the path to the html template.
    email_template_name : str
        defines the path of the email content file.
    subject_template_name : str
        defines the path of the email subject file.
    succes_url : str
        url if the password reset was a success.
    """
    template_name = 'user/password_reset/form.html'
    email_template_name = 'user/password_reset/email.html'
    subject_template_name = 'user/password_reset/subject.txt'
    success_url = 'done/'


class ResetDoneView(PasswordResetDoneView):
    """inherits from PasswordResetDoneView and modifies some values
    Attributes
    ----------
    template_name : str
        defines the path to the html template.
    """
    template_name = 'user/password_reset/done.html'


class ResetConfirmView(PasswordResetConfirmView):
    """inherits from PasswordResetConfirm and modifies some values
    Attributes
    ----------
    template_name : str
        defines the path to the html template.
    succes_url : str
        url if the password reset was a success.
    """
    template_name = 'user/password_reset/confirm.html'
    success_url = '/user/reset/done'


class ResetCompleteView(PasswordResetCompleteView):
    """inherits from PasswordResetCompleteView and modifies some values
    Attributes
    ----------
    template_name : str
        defines the path to the html template.
    """
    template_name = 'user/password_reset/complete.html'


# Thanks to: https://stackoverflow.com/questions/1392413/calculating-a-
# directorys-size-using-python
def user_storage_space(start_path = '.'):
    """
    Calculates the storage space that the user's file occupy in byte.

    Parameters
    ----------
    start_path : String
        The path to the directory of the user.
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    total_size = convert_size(total_size)
    return total_size

# Thanks to: https://stackoverflow.com/questions/5194057/better-way-to-convert-
# file-sizes-in-python
def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])
