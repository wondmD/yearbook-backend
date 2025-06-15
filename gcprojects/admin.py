from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin interface for the Project model."""
    list_display = ('title', 'user', 'is_featured', 'created_at', 'updated_at')
    list_filter = ('is_featured', 'created_at', 'updated_at', 'user')
    search_fields = ('title', 'description', 'user__username', 'technologies')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ()
    ordering = ('-is_featured', '-created_at')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'user')
        }),
        (_('URLs'), {
            'fields': ('code_url', 'live_url', 'image_url')
        }),
        (_('Additional Info'), {
            'fields': ('technologies', 'is_featured')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Return a QuerySet of all projects."""
        return super().get_queryset(request).select_related('user')
    
    def save_model(self, request, obj, form, change):
        """Save the model and set the user if not set."""
        if not obj.user and request.user.is_authenticated:
            obj.user = request.user
        super().save_model(request, obj, form, change)
