from rest_framework import status, permissions, generics, filters, serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import connection
from django.db.models import Q
from django.conf import settings
import os
from .models import UserProfile
from django.db import transaction

from .serializers import (
    UserSerializer, 
    RegisterSerializer,
    UserProfileSerializer
)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """View for user registration."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        return user

class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating user profile."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        # Get the profile of the currently authenticated user
        return self.request.user.profile

class UserDetailView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating user and profile details."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    http_method_names = ['get', 'post', 'put', 'patch']  # Explicitly allow POST

    def get_object(self):
        return self.request.user
    
    def post(self, request, *args, **kwargs):
        # For POST requests, use the same logic as update
        return self.update(request, *args, **kwargs)
        
    def update(self, request, *args, **kwargs):
        print("Request data:", request.data)  # Debug log
        
        # Get the user instance
        user = self.get_object()
        data = request.data.copy()
        
        # Handle profile data if it's nested under 'profile' key
        profile_data = {}
        if 'profile' in data:
            profile_data = data.pop('profile')
        
        # Also check if profile fields are at the root level
        profile_fields = [
            'nickname', 'bio', 'location', 'interests',
            'image', 'fun_fact', 'social_links'
        ]
        
        # Move any root-level profile fields to profile_data
        for field in profile_fields:
            if field in data:
                profile_data[field] = data.pop(field)
        
        # Update user data first
        user_serializer = self.get_serializer(
            user,
            data=data,
            partial=True
        )
        
        if not user_serializer.is_valid():
            print("User serializer errors:", user_serializer.errors)
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Save user data
        user = user_serializer.save()
        
        # Now handle profile data if it exists
        if profile_data:
            # Get the profile instance
            profile = user.profile
            
            # Handle image specially if it's a URL
            if 'image' in profile_data and isinstance(profile_data['image'], str):
                # If it's a URL, update the image field directly
                profile.image = profile_data.pop('image')
            
            # Update other profile fields
            profile_serializer = UserProfileSerializer(
                profile,
                data=profile_data,
                partial=True,
                context=self.get_serializer_context()
            )
            
            if not profile_serializer.is_valid():
                print("Profile serializer errors:", profile_serializer.errors)
                return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            profile_serializer.save()
        
        # Return the updated user with profile
        serializer = self.get_serializer(user)
        return Response(serializer.data)

class UserListView(generics.ListAPIView):
    """View for listing all users (admin only)."""
    permission_classes = []  # Temporarily disabled for debugging
    authentication_classes = []  # Temporarily disabled for debugging
    serializer_class = UserSerializer
    
    def get_queryset(self):
        # Get all users for debugging
        all_users = User.objects.all()
        print("\n=== DEBUGGING USERLISTVIEW ===")
        print(f"Request path: {self.request.path}")
        print(f"URL kwargs: {self.kwargs}")
        print(f"Query params: {self.request.query_params}")
        
        # Print all users in database
        print("\nAll users in database:")
        for user in all_users:
            print(f"- {user.username} (ID: {user.id}, is_approved: {user.is_approved})")
        
        # Filter unapproved users
        queryset = User.objects.filter(is_approved=False)
        print("\nFiltered users (is_approved=False):")
        for user in queryset:
            print(f"- {user.username} (ID: {user.id})")
        
        # Print serialized data
        print("\nSerialized data:")
        serializer = self.get_serializer(queryset, many=True)
        print(serializer.data)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Override list method to add debug info
        print("\n=== LIST METHOD ===")
        queryset = self.filter_queryset(self.get_queryset())
        
        # Print final queryset
        print("\nFinal queryset count:", queryset.count())
        for user in queryset:
            print(f"- {user.username} (ID: {user.id}, is_approved: {user.is_approved})")
        
        # Serialize the data
        serializer = self.get_serializer(queryset, many=True)
        print("\nSerialized data in list method:", serializer.data)
        
        # Return the response with debug info
        response_data = {
            'success': True,
            'count': queryset.count(),
            'users': serializer.data,
            'debug': {
                'path': request.path,
                'method': request.method,
                'query_params': dict(request.query_params),
                'url_kwargs': dict(kwargs)
            }
        }
        
        print("\nFinal response data:", response_data)
        return Response(response_data)


class UserManagementView(APIView):
    """View for managing user approval status (admin only)."""
    permission_classes = [IsAdminUser]

    def get_user(self, user_id):
        return get_object_or_404(User, id=user_id)
    
    def post(self, request, user_id, action):
        user = self.get_user(user_id)
        
        if action == 'approve':
            return self._approve_user(user)
        elif action == 'reject':
            return self._reject_user(user)
        else:
            return Response(
                {"error": "Invalid action"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _approve_user(self, user):
        if user.is_approved:
            return Response(
                {"message": f"User {user.username} is already approved."},
                status=status.HTTP_200_OK
            )
            
        user.is_approved = True
        user.save()
        
        # Here you might want to send an email notification
        # to the user about their approval
        
        return Response(
            {"message": f"User {user.username} has been approved successfully."},
            status=status.HTTP_200_OK
        )
    
    def _reject_user(self, user):
        # Instead of deleting, we can deactivate the account
        # and keep it for record-keeping
        if not user.is_active:
            return Response(
                {"message": f"User {user.username} is already deactivated."},
                status=status.HTTP_200_OK
            )
            
        user.is_active = False
        user.save()
        
        # Here you might want to send an email notification
        # to the user about their rejection
        
        return Response(
            {"message": f"User {user.username} has been rejected and deactivated."},
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def debug_unapproved_users(request):
    """Debug endpoint to test unapproved users query"""
    print("\n=== DEBUG UNNPROVED USERS ===")
    
    # Get all users
    all_users = list(User.objects.all().values('id', 'username', 'is_approved'))
    print("All users:", all_users)
    
    # Get unapproved users
    unapproved = list(User.objects.filter(is_approved=False).values('id', 'username'))
    print("Unapproved users:", unapproved)
    
    # Get approved users
    approved = list(User.objects.filter(is_approved=True).values('id', 'username'))
    print("Approved users:", approved)
    
    # Raw SQL query
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, username, is_approved FROM users_user WHERE is_approved = %s", [False])
        raw_results = cursor.fetchall()
        print("Raw SQL results:", raw_results)
    
    return Response({
        'all_users': all_users,
        'unapproved_users': unapproved,
        'approved_users': approved,
        'raw_sql_results': raw_results
    })

# For backward compatibility
class ApproveUserView(APIView):
    """Legacy view for approving users (kept for backward compatibility)."""
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user.is_approved = True
        user.save()
        return Response(
            {"message": f"User {user.username} has been approved."},
            status=status.HTTP_200_OK
        )

class BlacklistTokenView(APIView):
    """View for logging out a user by blacklisting their refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class CheckAuthView(APIView):
    """View to check if user is authenticated and get their data."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class ProfileListView(generics.ListAPIView):
    """View for listing user profiles."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    queryset = UserProfile.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'nickname']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter out unapproved users
        return queryset.filter(user__is_approved=True)


class IsOwnerOrStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it,
    but allow read-only access to approved profiles for everyone.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request for approved profiles
        if request.method in permissions.SAFE_METHODS and obj.is_approved:
            return True
            
        # Write permissions are only allowed to the owner or staff
        return obj.user == request.user or request.user.is_staff


class ProfileViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user profiles.
    Each user can have exactly one profile.
    Approved profiles are visible to everyone, including unauthenticated users.
    """
    permission_classes = [IsAuthenticated]  # Require authentication for all operations
    serializer_class = UserProfileSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]  # Anyone can view approved profiles
        else:
            permission_classes = [IsAuthenticated]  # Need to be authenticated for other actions
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Return profiles based on user permissions and filters.
        - Staff can see all profiles
        - Regular users can see all approved profiles and their own profile (if unapproved)
        - Unauthenticated users can only see approved profiles
        """
        user = self.request.user
        queryset = UserProfile.objects.all()
        
        # For unauthenticated users, only show approved profiles
        if not user.is_authenticated:
            return queryset.filter(is_approved=True).order_by('-created_at')
            
        # For staff, show all profiles
        if user.is_staff:
            return queryset.order_by('-created_at')
            
        # For regular authenticated users, show approved profiles and their own profile
        queryset = queryset.filter(Q(is_approved=True) | Q(user=user))
        
        # Apply search if provided
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(nickname__icontains=search)
            )
        
        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        # Check if user already has a profile
        if UserProfile.objects.filter(user=request.user).exists():
            raise serializers.ValidationError({"detail": "You already have a profile."})
            
        # Check if user is approved (shouldn't happen due to permissions, but just in case)
        if not request.user.is_approved and not request.user.is_staff:
            raise serializers.ValidationError({"detail": "Your account is not approved. Please wait for admin approval before creating a profile."})
            
        return super().create(request, *args, **kwargs)
        
    def perform_create(self, serializer):
        """Create a new profile with approval status set to False."""
        serializer.save(user=self.request.user, is_approved=False)
        
    def check_object_permissions(self, request, obj):
        """Check if user has permission to perform the action on the object."""
        super().check_object_permissions(request, obj)
        
        # For write operations, check if the user is the owner or staff
        if request.method not in permissions.SAFE_METHODS:
            if obj.user != request.user and not request.user.is_staff:
                self.permission_denied(
                    request,
                    message="You do not have permission to perform this action.",
                    code=status.HTTP_403_FORBIDDEN
                )
                
            # Check if the user is approved for non-read operations
            if not request.user.is_approved and not request.user.is_staff:
                self.permission_denied(
                    request,
                    message="Your account is not approved. Please wait for admin approval before making changes.",
                    code=status.HTTP_403_FORBIDDEN
                )

    def get_object(self):
        """
        Return the profile for detail view.
        Allows access to approved profiles for everyone, including unauthenticated users.
        """
        user = self.request.user
        
        # If no pk is provided and user is authenticated, return their own profile
        if 'pk' not in self.kwargs:
            if user.is_authenticated:
                return user.profile
            raise PermissionDenied("Authentication required to view your profile")
            
        # Get the requested profile
        profile = get_object_or_404(UserProfile, pk=self.kwargs['pk'])
        
        # Allow access if:
        # 1. Profile is approved (visible to everyone, including unauthenticated users)
        # 2. User is staff (can see all profiles)
        # 3. User is viewing their own profile (even if unapproved)
        if profile.is_approved or (user.is_authenticated and (user.is_staff or profile.user == user)):
            return profile
            
        raise PermissionDenied("You don't have permission to view this profile.")


class PendingProfilesView(APIView):
    """View for listing and managing pending profiles (admin only)."""
    permission_classes = [IsAdminUser]
    
    def get(self, request, format=None):
        """Get a list of all profiles pending approval."""
        try:
            profiles = UserProfile.objects.filter(is_approved=False).select_related('user')
            serializer = UserProfileSerializer(profiles, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ApproveProfileView(APIView):
    """View for approving a profile (admin only)."""
    permission_classes = [IsAdminUser]
    
    def post(self, request, profile_id, format=None):
        """Approve a profile by ID."""
        try:
            with transaction.atomic():
                profile = get_object_or_404(UserProfile, id=profile_id)
                profile.is_approved = True
                profile.save()
                
                # Also approve the user if not already approved
                if not profile.user.is_approved:
                    profile.user.is_approved = True
                    profile.user.save()
                
                serializer = UserProfileSerializer(profile, context={'request': request})
                return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RejectProfileView(APIView):
    """View for rejecting a profile (admin only)."""
    permission_classes = [IsAdminUser]
    
    def post(self, request, profile_id, format=None):
        """Reject a profile by ID."""
        try:
            with transaction.atomic():
                profile = get_object_or_404(UserProfile, id=profile_id)
                
                # Delete the profile image if it exists
                if profile.image:
                    profile.image.delete(save=False)
                
                # Delete the profile
                profile.delete()
                
                return Response(
                    {'message': 'Profile rejected and deleted successfully'},
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProfileImageView(APIView):
    """View for handling profile image uploads."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def _get_absolute_media_url(self, request, path):
        """Generate absolute media URL."""
        # Remove any leading /media/ if present
        if path.startswith('/media/'):
            path = path[7:]
        elif path.startswith('media/'):
            path = path[6:]
            
        # Return just the relative path (frontend will handle the base URL)
        return f"/media/{path}"
        
        # Uncomment below if you need absolute URLs in the response
        # Make sure to only include the base URL without duplicating /media/
        # base_url = f"{request.scheme}://{request.get_host()}"
        # return f"{base_url}/media/{path}"

    def post(self, request, format=None):
        if 'image' not in request.FILES:
            print("Error: No image file provided in request.FILES")
            return Response(
                {'error': 'No image file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            print(f"Processing image upload for user: {request.user.username}")
            print(f"Uploaded file: {request.FILES['image'].name} (size: {request.FILES['image'].size} bytes)")
            
            # Get or create user profile
            try:
                profile, created = UserProfile.objects.get_or_create(user=request.user)
                print(f"Profile {'created' if created else 'retrieved'}: {profile.id}")
            except Exception as e:
                error_msg = f"Error getting/creating profile: {str(e)}"
                print(error_msg)
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # If user already has a profile image, delete the old one
            if profile.image:
                print(f"Deleting old image: {profile.image.path}")
                try:
                    profile.image.delete(save=False)
                except Exception as e:
                    print(f"Warning: Could not delete old image: {str(e)}")

            # Save the new image
            try:
                profile.image = request.FILES['image']
                profile.save()
                print(f"New image saved to: {profile.image.path}")
                
                # Get the relative URL
                image_url = profile.image.url
                print(f"Generated image URL: {image_url}")

                # Return the full relative URL
                # The URL is already in the format /media/profile_images/user_<id>/filename
                # Just remove the leading slash to make it relative
                if image_url.startswith('/'):
                    image_url = image_url[1:]
                    
                return Response({
                    'url': image_url,
                    'message': 'Image uploaded successfully'
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                error_msg = f"Error saving image: {str(e)}"
                print(error_msg)
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(error_msg)
            return Response(
                {'error': 'Failed to process image upload', 'details': error_msg}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
