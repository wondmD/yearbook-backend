from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.management import call_command

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser with approved status'

    def handle(self, *args, **options):
        # First, create the superuser using the default createsuperuser command
        call_command('createsuperuser')
        
        # Get the most recently created user (should be the one just created)
        user = User.objects.order_by('-date_joined').first()
        
        if user:
            # Set the user as approved
            user.is_approved = True
            user.save(update_fields=['is_approved'])
            self.stdout.write(
                self.style.SUCCESS(f'Successfully set {user.username} as approved')
            )
