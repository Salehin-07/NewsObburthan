from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import AccountProfile


# ── Inline profile inside User admin ──────────────────────────────────────────
class AccountProfileInline(admin.StackedInline):
    model   = AccountProfile
    can_delete = False
    verbose_name_plural = 'Staff Profile'
    fk_name = 'user'

    fieldsets = (
        ('Personal', {
            'fields': ('profile_image', 'phone', 'bio', 'designation', 'department', 'personal_email'),
        }),
        ('Social', {
            'fields': ('twitter_handle', 'facebook_url', 'linkedin_url'),
            'classes': ('collapse',),
        }),
        ('Roles', {
            'fields': ('is_reporter', 'is_editor', 'is_columnist', 'is_photographer', 'is_admin', 'is_active_staff'),
        }),
        ('Employment', {
            'fields': ('employee_id', 'joining_date'),
            'classes': ('collapse',),
        }),
    )


# ── Extend the built-in User admin ───────────────────────────────────────────
class UserAdmin(BaseUserAdmin):
    inlines = (AccountProfileInline,)
    list_display  = ('username', 'email', 'get_full_name', 'get_roles', 'is_staff', 'is_active')
    list_select_related = ('account_profile',)

    @admin.display(description='Roles')
    def get_roles(self, obj):
        if hasattr(obj, 'account_profile'):
            return obj.account_profile.roles_display
        return '—'


# Re-register User with the extended admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ── Standalone AccountProfile admin ──────────────────────────────────────────
@admin.register(AccountProfile)
class AccountProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'designation', 'department', 'is_reporter', 'is_editor', 'is_admin', 'is_active_staff', 'credits')
    list_filter   = ('is_reporter', 'is_editor', 'is_admin', 'is_active_staff', 'department')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'designation', 'department')
    raw_id_fields = ('user',)

    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Personal', {
            'fields': ('profile_image', 'phone', 'bio', 'designation', 'department', 'personal_email', 'credits'),
        }),
        ('Social', {
            'fields': ('twitter_handle', 'facebook_url', 'linkedin_url'),
        }),
        ('Roles & Access', {
            'fields': ('is_reporter', 'is_editor', 'is_columnist', 'is_photographer', 'is_admin', 'is_active_staff'),
        }),
        ('Employment', {
            'fields': ('employee_id', 'joining_date'),
        }),
    )
