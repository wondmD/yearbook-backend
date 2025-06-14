from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer to include additional user data in the token.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Get the standard token data
        refresh = self.get_token(self.user)
        
        # Add user data to the response
        data.update({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'is_approved': self.user.is_approved,
                'is_admin': self.user.is_staff or self.user.is_superuser,  # Map Django's is_staff to is_admin
                'is_staff': self.user.is_staff,
                'is_superuser': self.user.is_superuser,
            }
        })
        
        # Add profile data if available
        if hasattr(self.user, 'profile'):
            profile = self.user.profile
            data['user'].update({
                'student_id': getattr(profile, 'student_id', None),
                'batch': getattr(profile, 'batch', None),
                'image': profile.image.url if profile.image else None,
            })
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view that uses our custom token serializer.
    """
    serializer_class = CustomTokenObtainPairSerializer
