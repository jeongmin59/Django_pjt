from django.contrib import admin
from .models import DepositProducts, DepositOptions

# Register your models here.
admin.site.register(DepositProducts)
admin.site.register(DepositOptions)