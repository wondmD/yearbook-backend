from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class User(AbstractUser):
    """Custom User model with approval status for content creation."""
    is_approved = models.BooleanField(
        _('approved'),
        default=False,
        help_text=_('Designates whether the user is approved to add content.'),
    )
    student_id = models.CharField(
        _('student ID'),
        max_length=50,
        blank=True,
        help_text=_('Student identification number'),
    )
    batch = models.CharField(
        _('batch'),
        max_length=50,
        blank=True,
        help_text=_('Graduation batch/year'),
    )
    role = models.CharField(
        _('role'),
        max_length=50,
        blank=True,
        help_text=_('User role (e.g., student, admin)'),
    )

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['username']

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    """Extended user profile information."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    nickname = models.CharField(
        _('nickname'),
        max_length=100,
        blank=True,
        help_text=_('A fun nickname or title'),
    )
    bio = models.TextField(
        _('bio'),
        blank=True,
        help_text=_('A short biography or description'),
    )
    location = models.CharField(
        _('location'),
        max_length=200,
        blank=True,
        help_text=_('Current location'),
    )
    interests = models.JSONField(
        _('interests'),
        default=list,
        help_text=_('List of interests or skills'),
    )
    image = models.ImageField(
        _('profile image'),
        upload_to='profile_images/',
        blank=True,
        null=True,
        help_text=_('Profile picture'),
    )
    fun_fact = models.TextField(
        _('fun fact'),
        blank=True,
        help_text=_('A fun or interesting fact about the user'),
    )
    social_links = models.JSONField(
        _('social links'),
        default=dict,
        help_text=_('Dictionary of social media links'),
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.username}'s profile"
