from django.shortcuts import render
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Project
from .serializers import ProjectSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter

# Create your views here.

class ProjectFilter(FilterSet):
    """Custom filter for Project model."""
    technologies = CharFilter(method='filter_technologies')

    class Meta:
        model = Project
        fields = ['is_featured', 'technologies']

    def filter_technologies(self, queryset, name, value):
        """Filter projects by technology."""
        if not value:
            return queryset
        return queryset.filter(technologies__contains=[value])


@extend_schema(tags=['Projects'])
class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing projects.
    
    Projects are publicly accessible and can be created without authentication.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectFilter  # Use our custom filter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-is_featured', '-created_at']
    
    @extend_schema(
        description='List all projects with optional filtering',
        parameters=[
            OpenApiParameter(
                name='is_featured',
                type=bool,
                description='Filter by featured status'
            ),
            OpenApiParameter(
                name='technologies',
                type=str,
                description='Filter by technology (comma-separated)'
            ),
            OpenApiParameter(
                name='search',
                type=str,
                description='Search in title, description, and technologies'
            ),
            OpenApiParameter(
                name='ordering',
                type=str,
                description='Order by field (prefix with - for descending)'
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """List all projects with optional filtering."""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        description='Create a new project',
        request=ProjectSerializer,
        responses={201: ProjectSerializer}
    )
    def create(self, request, *args, **kwargs):
        """Create a new project."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def perform_create(self, serializer):
        """Create a new project with optional user association."""
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)
    
    @extend_schema(
        description='Get featured projects',
        responses={200: ProjectSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get all featured projects."""
        projects = self.get_queryset().filter(is_featured=True)
        serializer = self.get_serializer(projects, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description='Filter projects by technology',
        parameters=[
            OpenApiParameter(
                name='technology',
                type=str,
                required=True,
                description='Technology to filter by'
            )
        ],
        responses={200: ProjectSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='by_technology')
    def by_technology(self, request):
        """
        Filter projects by technology.
        
        Parameters:
        - technology (str): The technology to filter by (e.g., 'django', 'react', etc.)
        
        Returns:
        - List of projects that use the specified technology
        """
        technology = request.query_params.get('technology', '').lower()
        if not technology:
            return Response(
                {"error": "Please provide a technology parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Get all projects and filter in Python since SQLite doesn't support JSON contains
        projects = self.get_queryset()
        filtered_projects = [
            project for project in projects 
            if project.technologies and 
            any(tech.lower() == technology for tech in project.technologies)
        ]
        
        serializer = self.get_serializer(filtered_projects, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description='Get projects by user',
        parameters=[
            OpenApiParameter(
                name='username',
                type=str,
                required=True,
                description='Username to filter by'
            )
        ],
        responses={200: ProjectSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='by_user')
    def by_user(self, request):
        """Get projects created by a specific user."""
        username = request.query_params.get('username')
        if not username:
            return Response(
                {'error': 'Username parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        projects = self.get_queryset().filter(
            user__username=username
        )
        serializer = self.get_serializer(projects, many=True)
        return Response(serializer.data)
