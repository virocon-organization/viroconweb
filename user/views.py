from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import auth
from django.http import HttpResponseRedirect
from .forms import CustomUserCreationForm
from .forms import CustomUserEditForm
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.contrib.auth import update_session_auth_hash


# Method will be opened when login button is pressed and opens the login html
def authentication(request):
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
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        # user will be saved in db, if input is form-compliant, else a error site opens
        if form.is_valid():
            form.save()
            authentic(request, username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            return HttpResponseRedirect('/home')
        else:
            return render(request, 'user/create.html', {'form': form})
    # provides fields to be filled
    else:
        return render(request, 'user/create.html', {'form': CustomUserCreationForm()})


# Method called at logout and logs user off
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/home')


# Method shows user profile
def profile(request):
    return render(request, 'user/profile.html')


def edit(request):
    if request.method == 'POST':
        form = CustomUserEditForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            return redirect(reverse('user:profile'))
    else:
        form = CustomUserEditForm(instance=request.user)
        return render(request, 'user/edit.html', {'form': form})


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(data=request.POST, user=request.user)

        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return redirect(reverse('user:profile'))
        else:
            return render(request, 'user/change_password.html', {'form': form})
    else:
        form = PasswordChangeForm(user=request.user)
        return render(request, 'user/change_password.html', {'form': form})
