from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserPreference

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'name', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_staff']
    search_fields = ['email', 'name']
    ordering = ['-created_at']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('name', 'phone', 'profile_image')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = ((None, {'fields': ('email', 'name', 'password1', 'password2')}),)

admin.register(UserPreference)(type('UserPreferenceAdmin', (admin.ModelAdmin,), {'list_display': ['user', 'spice_level', 'budget_range']}))
