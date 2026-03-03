from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import User


# -------------------------
# Custom User Creation Form
# -------------------------
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'role',
            'phone',
            'address',
            'salary',
            'profile_picture',
        )


# -------------------------
# Custom User Change Form
# -------------------------
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


# -------------------------
# Custom User Admin
# -------------------------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    model = User

    list_display = (
        'email',
        'first_name',
        'last_name',
        'role',
        'employee_id',
        'is_staff',
        'is_active',
    )

    list_filter = (
        'role',
        'is_staff',
        'is_active',
    )

    ordering = ('-date_joined',)
    search_fields = ('email', 'first_name', 'last_name', 'employee_id')

    readonly_fields = ('employee_id', 'date_joined')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': (
                'first_name',
                'last_name',
                'phone',
                'address',
                'profile_picture',
            )
        }),
        ('Employment Info', {
            'fields': (
                'role',
                'employee_id',
                'salary',
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'first_name',
                'last_name',
                'role',
                'password1',
                'password2',
                'is_staff',
                'is_superuser',
            ),
        }),
    )