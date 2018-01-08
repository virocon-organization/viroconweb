from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import auth
from django.http import HttpResponseRedirect
from .forms import CustomUserCreationForm
from .forms import CustomUserEditForm
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.contrib.auth import update_session_auth_hash


def authentication(request):
    """
    Thr method to login users.
    Parameters
    ----------
    request : to authenticate the user.

    Returns
    -------
    HttpResponse
    """
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(None, request.POST or None)
        if form.is_valid():
            auth.login(request, form.get_user())
            return HttpResponseRedirect('/home')
        else:
            return render(request, 'user/login.html', {'form': form})

    return render(request, 'user/login.html', {'form': form})


# Method is called after userdata is entered and checks database for verification
def authentic(request, username, password):
    user = auth.authenticate(username=username, password=password)
    auth.login(request, user)


def create(request):
    """
    The method creates a new user account .

    Parameters
    ----------
    request : to create a new user account.

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
    """
    The method logs out a user.

    Parameters
    ---------
    request : to log out.


    Return
    ------
    HttpResponseRedirect to home.
    """
    if request.user.is_anonymous:
        return HttpResponseRedirect('/home')
    else:
        auth.logout(request)
        return HttpResponseRedirect('/home')


def profile(request):
    """
    The method views the user profile.

    Parameters
    ----------
    request : to view the user profile.

    Returns
    -------
    HttpResponse
    """
    if request.user.is_anonymous:
        return HttpResponseRedirect('/home')
    else:
        return render(request, 'user/profile.html')


def edit(request):
    """
    The method allows users to edit their profiles.

    Parameters
    ---------
    request : request to edit a user profile.

    Returns
    -------
    HttpResponse
    """
    if request.user.is_anonymous:
        return HttpResponseRedirect('/home')
    else:
        if request.method == 'POST':
            form = CustomUserEditForm(request.POST, instance=request.user)

            if form.is_valid():
                form.save()
                return redirect(reverse('user:profile'))
        else:
            form = CustomUserEditForm(instance=request.user)
            return render(request, 'user/edit.html', {'form': form})


def change_password(request):
    """
    The method allows a user to change his password.

    Parameters
    ----------
    request : to change the user password

    Returns
    -------
    HttpResponse
    """
    if request.user.is_anonymous:
        return HttpResponseRedirect('/home')
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
