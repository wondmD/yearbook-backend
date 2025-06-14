from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from rest_framework.permissions import IsAuthenticated
from . import views
from .jwt_serializers import CustomTokenObtainPairView

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'profiles', views.ProfileViewSet, basename='profile')

# Admin endpoints
admin_patterns = [
    # User management
    path('users/', views.UserListView.as_view(), name='admin_user_list'),
    path('users/unapproved/', views.UserListView.as_view(), name='admin_unapproved_users', 
        kwargs={'is_approved': False}),
    path('users/<int:user_id>/<str:action>/', views.UserManagementView.as_view(), 
        name='admin_manage_user'),
    
    # Backward compatibility
    path('users/<int:user_id>/approve/', views.ApproveUserView.as_view(), name='approve_user'),
]

# Include router URLs first to avoid conflicts
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Debug endpoint
    path('debug/unapproved/', views.debug_unapproved_users, name='debug_unapproved_users'),
    
    # Authentication endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('token/blacklist/', views.BlacklistTokenView.as_view(), name='token_blacklist'),
    
    # User profile endpoints
    path('users/profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('users/profile/image/', views.ProfileImageView.as_view(), name='profile_image_upload'),
    path('users/me/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/check-auth/', views.CheckAuthView.as_view(), name='check_auth'),
    
    # Profile approval endpoints
    path('admin/profiles/pending/', views.PendingProfilesView.as_view(), name='pending_profiles'),
    path('admin/profiles/<int:profile_id>/approve/', views.ApproveProfileView.as_view(), name='approve_profile'),
    path('admin/profiles/<int:profile_id>/reject/', views.RejectProfileView.as_view(), name='reject_profile'),
    
    # Admin endpoints
    path('admin/', include((admin_patterns, 'admin'))),
    
    # Backward compatibility
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:user_id>/approve/', views.ApproveUserView.as_view(), name='approve_user_deprecated'),
    
    # Keep this at the end to avoid conflicts
    path('profiles/', views.ProfileListView.as_view(), name='profile_list'),
]

# Add URL patterns for the API documentation
app_name = 'users'  # This is the app's namespace
