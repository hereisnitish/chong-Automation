from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import Dashboard, EmailFolder, UserData, LogEntry, Lead  # <-- import your new model

User = get_user_model()


# ---------- Inlines ----------
class UserDataInline(admin.StackedInline):
    model = UserData
    can_delete = False
    fk_name = 'user'
    extra = 0
    fields = ('company_name', 'mc_number', 'number_of_trucks', 'phone_number')
    verbose_name = "User Data"
    verbose_name_plural = "User Data"


# ---------- User Admin ----------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin for your custom User model.
    Assumes User extends AbstractUser with 'email' as USERNAME_FIELD and has 'phone_number'.
    Company-related fields now live in UserData and are shown via inline + helper columns.
    """

    # Helper methods to show UserData fields in list_display
    def company_name(self, obj):
        return getattr(getattr(obj, 'user_data', None), 'company_name', None)
    company_name.short_description = 'Company'

    def mc_number(self, obj):
        return getattr(getattr(obj, 'user_data', None), 'mc_number', None)
    mc_number.short_description = 'MC #'

    def number_of_trucks(self, obj):
        return getattr(getattr(obj, 'user_data', None), 'number_of_trucks', None)
    number_of_trucks.short_description = '# Trucks'

    # Columns in the list page
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'phone_number', 'company_name', 'mc_number', 'number_of_trucks',
        'is_staff', 'is_active',
    )

    list_filter = (
        'is_staff', 'is_superuser', 'is_active', 'groups',
    )

    search_fields = (
        'username', 'email', 'first_name', 'last_name', 'phone_number',
        # allow searching into the related UserData
        'user_data__company_name', 'user_data__mc_number',
    )

    ordering = ('-date_joined',)

    # Detail page (change view)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        # Company fields removed from here; handled by the inline below
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Create page (add view)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'first_name', 'last_name',
                'phone_number', 'password1', 'password2',
            ),
        }),
        ('Permissions', {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
    )

    inlines = [UserDataInline]


# ---------- UserData Admin (optional but useful) ----------
@admin.register(UserData)
class UserDataAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'company_name', 'mc_number', 'number_of_trucks', 'phone_number', 'created_at')
    search_fields = ('user__email', 'company_name', 'mc_number', 'phone_number')
    list_filter = ('company_name',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    def user_email(self, obj):
        return getattr(obj.user, 'email', None)
    user_email.short_description = 'User Email'


# ---------- Dashboard Admin ----------
@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['email', 'phone_number', 'type', 'created_date', 'user']
    list_filter = ['type', 'created_date']
    search_fields = ['email', 'phone_number', 'user__email', 'user__username']
    date_hierarchy = 'created_date'
    ordering = ['-created_date']


# ---------- EmailFolder Admin ----------
@admin.register(EmailFolder)
class EmailFolderAdmin(admin.ModelAdmin):
    list_display = ['email', 'folder_date', 'folder_year', 'folder_month', 'company_name_folder_id', 'created_at']
    list_filter = ['folder_year', 'folder_month', 'created_at']
    search_fields = ['email', 'company_name_folder_id', 'year_folder_id', 'month_folder_id', 'date_folder_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-folder_date']
    date_hierarchy = 'folder_date'


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'level', 'event', 'user']
    list_filter = ['level', 'created_at']
    search_fields = ['event', 'details', 'user__email']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'company_name', 'phone', 'email', 'status', 'created_at')
    list_filter = ('status', 'help_needed', 'created_at')
    search_fields = ('full_name', 'email', 'phone', 'company_name', 'mc_number')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)    
