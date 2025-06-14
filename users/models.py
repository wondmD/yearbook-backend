from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .utils import user_profile_image_path, validate_image_file_extension


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
    """Extended user profile information.
    
    Each user can have exactly one profile.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        unique=True,
        error_messages={
            'unique': 'A profile already exists for this user.'
        }
    )
    is_approved = models.BooleanField(
        _('approved'),
        default=False,
        help_text=_('Designates whether this profile is approved to be shown on the site.'),
    )
    
    def clean(self):
        """Ensure one profile per user."""
        if self.user_id and UserProfile.objects.filter(user=self.user).exclude(pk=self.pk).exists():
            raise ValidationError('A profile already exists for this user.')
    
    def save(self, *args, **kwargs):
        """Override save to call clean method."""
        self.clean()
        super().save(*args, **kwargs)
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
        upload_to=user_profile_image_path,
        blank=True,
        null=True,
        help_text=_('Profile picture'),
        validators=[validate_image_file_extension],
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
