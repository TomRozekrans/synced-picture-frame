from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from selector.models import Picture, PictureGroup, User, Device

# Register your models here.


admin.site.register(Picture)
admin.site.register(PictureGroup)
admin.site.register(User, UserAdmin)
admin.site.register(Device)
