from django.contrib import admin
from .models import User
from .forms import CustomUserAdmin

# register the custom User and the CustomUserAdmin.
admin.site.register(User, CustomUserAdmin)

