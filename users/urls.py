from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views
from .jwt_serializers import CustomTokenObtainPairView

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

urlpatterns = [
    # Debug endpoint
    path('debug/unapproved/', views.debug_unapproved_users, name='debug_unapproved_users'),
    
    # Authentication endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('token/blacklist/', views.BlacklistTokenView.as_view(), name='token_blacklist'),
    
    # User profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('me/', views.UserDetailView.as_view(), name='user_detail'),
    path('check-auth/', views.CheckAuthView.as_view(), name='check_auth'),
    
    # Admin endpoints
    path('admin/', include((admin_patterns, 'admin'))),
    
    # Backward compatibility
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:user_id>/approve/', views.ApproveUserView.as_view(), name='approve_user_deprecated'),
]

# Add URL patterns for the API documentation
app_name = 'users'  # This is the app's namespace
