from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import os

def event_image_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/events/event_<event_id>/<filename>
    if hasattr(instance, 'event') and instance.event_id:
        return f'events/event_{instance.event_id}/{filename}'
    return f'events/event_unknown/{filename}'

class Event(models.Model):
    CATEGORY_CHOICES = [
        ('MILESTONE', 'Milestone'),
        ('THEME_DAY', 'Theme Day'),
        ('ACADEMIC', 'Academic'),
        ('WELCOME', 'Welcome'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    date = models.DateField()
    location = models.CharField(max_length=200)
    description = models.TextField()
    attendees_count = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    photos_count = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    highlights = models.JSONField(default=list, help_text="List of event highlights")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    cover_image = models.ImageField(upload_to=event_image_path, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_events'
    )
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
    
    def __str__(self):
        return f"{self.title} ({self.get_category_display()}) - {self.date}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.title)}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)
        
        # Update photos count
        self.photos_count = self.photos.count()
        super().save(update_fields=['photos_count'])


class EventPhoto(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='photos',
        related_query_name='photo'
    )
    image = models.ImageField(upload_to=event_image_path)
    caption = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_event_photos'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Event Photo'
        verbose_name_plural = 'Event Photos'
    
    def __str__(self):
        return f"Photo for {self.event.title} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"
    
    def delete(self, *args, **kwargs):
        # Delete the image file when the photo is deleted
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)
