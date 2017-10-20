from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import auth
from django.http import HttpResponseRedirect
from .forms import RegistrationForm, LoginForm, EditProfileForm
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash


# Method will be opened when login button is pressed and opens the login html
def login(request):
    login_form = LoginForm()
    if request.method == 'POST':
        auth_form = LoginForm(None, request.POST or None)
        error_text = "Login Fehlgeschlagen"
        if auth_form.is_valid():
            auth.login(request, auth_form.get_user())
            return HttpResponseRedirect('/home')
        else:
            return render(request, 'user/user_login.html', {'error': error_text, 'form': login_form})

    return render(request, 'user/user_login.html', {'form': login_form})


# Method is called after userdata is entered and checks database for verification
def authentic(request, username, password):
    user = auth.authenticate(username=username, password=password)
    auth.login(request, user)


# Method is called after opening the registration html
def register_user(request):
    # opens after second call
    # processes data, input by user in the fields
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        # user will be saved in db, if input is form-compliant, else a error site opens
        print(form)
        if form.is_valid():
            form.save()
            authentic(request, username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            return HttpResponseRedirect('/home')
        else:
            return render(request, 'user/user_registration.html', {'form': form})
    # provides fields to be filled
    else:
        return render(request, 'user/user_registration.html', {'form': RegistrationForm()})


# Manages both html-files and redirects to correct site, depending on success or fail of registration
def register_form(request, err):
    if err is False:
        return render(request, 'user/user_registration.html', {'form': RegistrationForm()})
    else:
        return render(request, 'user/user_registration.html', {'form': RegistrationForm(),
            'error': "Register failed"} )


# Method called at logout and logs user off
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/home')


# Method shows user profile
def profile(request):
    return render(request, 'user/user_profile.html')


# Method makes user profile editable
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            return redirect(reverse('user:profile'))
    else:
        form = EditProfileForm(instance=request.user)
        args = {'form': form}
        for fields in form:
            print(fields)
        return render(request, 'user/user_edit_profile.html', args)


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(data=request.POST, user=request.user)

        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return redirect(reverse('user:profile'))
        else:
            return redirect('/user/change-password')
    else:
        form = PasswordChangeForm(user=request.user)
        args = {'form': form}
        return render(request, 'user/user_change_password.html', args)
