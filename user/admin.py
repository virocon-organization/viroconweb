"""Registers the custom User and the CustomUserAdmin.
"""
from django.contrib import admin
from .models import User
from .forms import CustomUserAdmin


admin.site.register(User, CustomUserAdmin)

