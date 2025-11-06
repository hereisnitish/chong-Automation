from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Dashboard, EmailFolder


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'is_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone_number',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('phone_number', 'email', 'first_name', 'last_name')}),
    )


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['email', 'phone_number', 'type', 'created_date', 'user']
    list_filter = ['type', 'created_date']
    search_fields = ['email', 'phone_number', 'user__email', 'user__username']
    date_hierarchy = 'created_date'
    ordering = ['-created_date']


@admin.register(EmailFolder)
class EmailFolderAdmin(admin.ModelAdmin):
    list_display = ['email', 'folder_date', 'folder_year', 'folder_month', 'email_folder_id', 'created_at']
    list_filter = ['folder_year', 'folder_month', 'created_at']
    search_fields = ['email', 'email_folder_id', 'year_folder_id', 'month_folder_id', 'date_folder_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-folder_date']
    date_hierarchy = 'folder_date'
