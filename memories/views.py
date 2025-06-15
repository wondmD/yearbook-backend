from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt import authentication as jwt_authentication
from django.db.models import Count, Q
from django.db import models
from .models import Memory
from .serializers import MemorySerializer

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners to edit their memories."""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.created_by == request.user

class MemoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows memories to be viewed or edited.
    """
    queryset = Memory.objects.all().order_by('-created_at')
    serializer_class = MemorySerializer
    
    # Set default authentication and permission classes
    authentication_classes = [jwt_authentication.JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]  # Add this line to handle file uploads
    
    def initialize_request(self, request, *args, **kwargs):
        """Initialize the request and set the action attribute."""
        # First, let the parent class initialize the request
        request = super().initialize_request(request, *args, **kwargs)
        
        # Set the action based on the request method
        method = request.method.lower()
        if method == 'get' and kwargs.get('pk'):
            self.action = 'retrieve'
        elif method == 'get':
            self.action = 'list'
        elif method == 'post':
            self.action = 'create'
        elif method in ['put', 'patch']:
            self.action = 'update'
        elif method == 'delete':
            self.action = 'destroy'
            
        return request
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        # Default to 'list' if action is not set
        action = getattr(self, 'action', 'list')
        
        print(f"\n=== GET_PERMISSIONS ===")
        print(f"Action: {action}")
        print(f"Request method: {getattr(self, 'request', None) and self.request.method or 'N/A'}")
        print(f"User: {getattr(self, 'request', None) and self.request.user or 'N/A'}")
        print(f"Authenticated: {getattr(self, 'request', None) and self.request.user.is_authenticated or 'N/A'}")
        
        # For list and retrieve, allow any (handled by IsAuthenticatedOrReadOnly)
        if action in ['list', 'retrieve']:
            print("Using default permissions (IsAuthenticatedOrReadOnly)")
            return super().get_permissions()
            
        # For create, update, partial_update, destroy, like actions, require authentication
        print("Using IsAuthenticated permission")
        return [permissions.IsAuthenticated()]
    
    def get_authenticators(self):
        # Default to 'list' if action is not set
        action = getattr(self, 'action', 'list')
        
        print(f"\n=== GET_AUTHENTICATORS ===")
        print(f"Action: {action}")
        print(f"Request method: {getattr(self, 'request', None) and self.request.method or 'N/A'}")
        
        # Always use JWT authentication for all actions
        # The permission classes will handle read vs write access
        return [jwt_authentication.JWTAuthentication()]

    def get_queryset(self):
        print("\n=== GET_QUERYSET ===")
        print(f"Action: {getattr(self, 'action', 'unknown')}")
        print(f"User: {self.request.user} (ID: {self.request.user.id if self.request.user.is_authenticated else 'anonymous'})")
        print(f"Authenticated: {self.request.user.is_authenticated}")
        print(f"Staff: {self.request.user.is_staff if self.request.user.is_authenticated else 'N/A'}")
        print(f"Request method: {self.request.method}")
        
        queryset = Memory.objects.all()
        user = self.request.user
        
        # For unauthenticated users, only show approved memories
        if not user.is_authenticated:
            print("Returning only approved memories (unauthenticated user)")
            return queryset.filter(is_approved=True).order_by('-created_at')
            
        # For authenticated non-staff users, show approved memories + their own unapproved memories
        if not user.is_staff:
            print("Returning approved + user's unapproved memories")
            return queryset.filter(
                models.Q(is_approved=True) | 
                models.Q(created_by=user, is_approved=False)
            ).order_by('-created_at')
            
        # For staff users, show all memories
        print("Returning all memories (staff user)")
        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        print("\n=== LIST MEMORIES ===")
        print(f"User: {request.user} (ID: {request.user.id if request.user.is_authenticated else 'anonymous'})")
        print(f"Authenticated: {request.user.is_authenticated}")
        print(f"Staff: {request.user.is_staff if request.user.is_authenticated else 'N/A'}")
        print(f"Headers: {dict(request.headers)}")
        print(f"Query params: {request.query_params}")
        
        # Log the queryset that will be used
        queryset = self.filter_queryset(self.get_queryset())
        print(f"Queryset count: {queryset.count()}")
        
        # Call the parent list method to handle pagination and serialization
        response = super().list(request, *args, **kwargs)
        
        print(f"Response status: {response.status_code}")
        print(f"Response data count: {len(response.data) if hasattr(response, 'data') and isinstance(response.data, list) else 'N/A'}")
        
        return response

    def create(self, request, *args, **kwargs):
        # Debug: Log request headers and authentication status
        print("\n=== CREATE MEMORY REQUEST ===")
        print(f"Request method: {request.method}")
        print(f"User authenticated: {request.user.is_authenticated}")
        print(f"User: {request.user}")
        print(f"Request user ID: {getattr(request.user, 'id', 'N/A')}")
        print(f"Request user class: {request.user.__class__.__name__}")
        print(f"Request auth: {request.auth}")
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request data keys: {list(request.data.keys()) if hasattr(request, 'data') else 'No data'}")
        
        # Check authentication first
        if not request.user.is_authenticated:
            print("\n=== AUTHENTICATION FAILED ===")
            print("User is not authenticated")
            return Response(
                {
                    'error': 'Authentication required',
                    'detail': 'You must be logged in to perform this action',
                },
                status=status.HTTP_401_UNAUTHORIZED,
                headers={'WWW-Authenticate': 'Bearer'}
            )
        
        # Check file size before processing
        if 'image' in request.FILES:
            image = request.FILES['image']
            # 5MB limit
            max_size = 5 * 1024 * 1024
            if image.size > max_size:
                return Response(
                    {'error': 'File size too large. Maximum size is 5MB.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Debug: Log request data
        print(f"Request data: {request.data}")
        print(f"Request files: {request.FILES}")
        
        try:
            # Initialize serializer with request data and context
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Debug: Log valid data
            print(f"Validated data: {serializer.validated_data}")
            
            # Create the memory
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            
            # Debug: Log success
            print("Memory created successfully")
            print("======================\n")
            
            return Response(
                serializer.data, 
                status=status.HTTP_201_CREATED, 
                headers=headers
            )
            
        except serializers.ValidationError as e:
            # Debug: Log validation error
            print(f"Validation error: {e}")
            print("======================\n")
            return Response(
                {'error': 'Validation error', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # Debug: Log unexpected error with traceback
            import traceback
            error_traceback = traceback.format_exc()
            print(f"Unexpected error: {str(e)}")
            print(f"Traceback: {error_traceback}")
            print("======================\n")
            return Response(
                {'error': 'An error occurred while creating the memory', 'details': str(e) if str(e) else 'Unknown error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        memory = self.get_object()
        user = request.user
        
        if memory.likes.filter(id=user.id).exists():
            memory.likes.remove(user)
            liked = False
        else:
            memory.likes.add(user)
            liked = True
            
        return Response({
            'liked': liked,
            'likes_count': memory.like_count
        })

    @action(detail=False, methods=['get'])
    def top_liked(self, request):
        """Get top 10 most liked memories"""
        queryset = self.get_queryset().annotate(
            likes_count=Count('likes')
        ).order_by('-likes_count')[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_memories(self, request):
        """Get memories created by the current user"""
        queryset = self.get_queryset().filter(created_by=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class AdminMemoryViewSet(viewsets.ModelViewSet):
    """
    Admin-only API endpoint for managing memories.
    """
    queryset = Memory.objects.all()
    serializer_class = MemorySerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return Memory.objects.all().order_by('-created_at')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a memory"""
        memory = self.get_object()
        memory.is_approved = True
        memory.save()
        return Response({'status': 'memory approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a memory"""
        memory = self.get_object()
        memory.delete()
        return Response({'status': 'memory rejected'})
