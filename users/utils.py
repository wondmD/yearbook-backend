import os
import uuid
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils import timezone


def user_profile_image_path(instance, filename):
    """
    Generate a file path for user profile images.
    The path will be: profile_images/user_<id>/<random_uuid>.<ext>
    """
    ext = os.path.splitext(filename)[1]  # Get the file extension
    filename = f"{uuid.uuid4()}{ext}"  # Generate a random filename
    return os.path.join('profile_images', f'user_{instance.user.id}', filename)


def validate_image_file_extension(value):
    """
    Validate that the uploaded file is an image.
    """
    import os
    from django.core.exceptions import ValidationError
    
    ext = os.path.splitext(value.name)[1]  # Get the file extension
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension. Please upload a valid image file.')


def get_user_from_request(request):
    """
    Helper function to get the user from the request.
    Returns None if the user is not authenticated.
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        return request.user
    return None


def is_user_approved(user):
    """
    Check if a user is approved to add content.
    """
    return user.is_authenticated and (user.is_staff or user.is_approved)
