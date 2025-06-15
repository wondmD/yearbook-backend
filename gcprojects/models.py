from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Project(models.Model):
    """Model for GC Projects.
    
    Each project can optionally be associated with a user.
    Projects are publicly accessible and can be created without authentication.
    """
    title = models.CharField(
        _('title'),
        max_length=200,
        help_text=_('The title of the project')
    )
    description = models.TextField(
        _('description'),
        help_text=_('Detailed description of the project')
    )
    code_url = models.URLField(
        _('code URL'),
        blank=True,
        help_text=_('URL to the project repository')
    )
    live_url = models.URLField(
        _('live URL'),
        blank=True,
        help_text=_('URL to the live demo')
    )
    image_url = models.URLField(
        _('image URL'),
        blank=True,
        help_text=_('URL to the project image')
    )
    technologies = models.JSONField(
        _('technologies'),
        default=list,
        help_text=_('List of technologies used in the project')
    )
    is_featured = models.BooleanField(
        _('featured'),
        default=False,
        help_text=_('Whether this project should be featured')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('user'),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects',
        help_text=_('The user who created this project')
    )
    
    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return self.title
