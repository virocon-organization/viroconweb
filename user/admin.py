from django.contrib import admin
#from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import CustomUserAdmin

admin.site.register(User, CustomUserAdmin)

