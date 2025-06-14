from rest_framework import status, permissions, generics, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import connection
from django.db.models import Q

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
    """View for retrieving and updating user details."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        # Get the currently authenticated user
        return self.request.user

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
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
