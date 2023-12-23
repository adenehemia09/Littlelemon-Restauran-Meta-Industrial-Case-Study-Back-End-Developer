from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import MenuItem, Category

admin.site.register(MenuItem)
admin.site.register(Category)



class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name')
    readonly_fields = ('id',)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)