from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_approved')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_approved')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    inlines = (UserProfileInline,)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'student_id', 'batch')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_approved', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nickname', 'location', 'is_approved', 'created_at')
    search_fields = ('user__username', 'nickname', 'location')
    list_filter = ('is_approved', 'created_at', 'updated_at')
    list_editable = ('is_approved',)
    actions = ['approve_profiles', 'unapprove_profiles']
    
    def approve_profiles(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} profiles were successfully approved.")
    approve_profiles.short_description = "Approve selected profiles"
    
    def unapprove_profiles(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} profiles were successfully unapproved.")
    unapprove_profiles.short_description = "Unapprove selected profiles"
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'nickname', 'bio', 'location', 'image')
        }),
        (_('Additional Info'), {
            'fields': ('interests', 'fun_fact', 'social_links')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
