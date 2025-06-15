from django.db import models
from django.conf import settings
from django.utils import timezone

class Memory(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Share your funny memory description here!")
    image = models.ImageField(upload_to='memories/images/', blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memories_created'
    )
    created_at = models.DateTimeField(default=timezone.now)
    is_approved = models.BooleanField(default=False)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_memories',
        blank=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Memories'

    def __str__(self):
        return f"{self.title} by {self.created_by.username}"

    @property
    def like_count(self):
        return self.likes.count()
