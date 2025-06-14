from django.contrib import admin
from django.utils.html import format_html
from .models import Event, EventPhoto

class EventPhotoInline(admin.TabularInline):
    model = EventPhoto
    extra = 1
    readonly_fields = ('preview_image',)
    fields = ('image', 'preview_image', 'caption', 'uploaded_by', 'is_approved')
    
    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px;" />',
                obj.image.url
            )
        return "No Image"
    preview_image.short_description = 'Preview'

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'location', 'is_approved', 'created_by')
    list_filter = ('is_approved', 'category', 'date')
    search_fields = ('title', 'description', 'location')
    inlines = [EventPhotoInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'category')
        }),
        ('Details', {
            'fields': ('date', 'location', 'attendees_count', 'photos_count')
        }),
        ('Media', {
            'fields': ('cover_image', 'highlights')
        }),
        ('Status', {
            'fields': ('is_approved', 'created_by', 'created_at', 'updated_at')
        }),
    )

@admin.register(EventPhoto)
class EventPhotoAdmin(admin.ModelAdmin):
    list_display = ('preview_image', 'event', 'uploaded_by', 'uploaded_at', 'is_approved')
    list_filter = ('is_approved', 'uploaded_at', 'event')
    search_fields = ('caption', 'event__title')
    list_editable = ('is_approved',)
    readonly_fields = ('preview_image', 'uploaded_at')
    
    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px;" />',
                obj.image.url
            )
        return "No Image"
    preview_image.short_description = 'Preview'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set uploaded_by on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
