from django.contrib import admin
from accounts.models import *
from rest_framework.authtoken.models import Token

admin.site.register(CustomUser)
admin.site.register(Subscribe)
