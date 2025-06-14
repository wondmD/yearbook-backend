from rest_framework import viewsets, status, filters, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404
import os

from .models import Event, EventPhoto
from .serializers import EventSerializer, EventCreateSerializer, EventPhotoSerializer
from users.permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly, IsApprovedUser

class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows events to be viewed or edited.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_approved']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date', 'created_at', 'attendees_count']
    ordering = ['-date']
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EventCreateSerializer
        return EventSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated, IsApprovedUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsApprovedUser, IsOwnerOrReadOnly]
        elif self.action in ['approve', 'unapprove']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Implements event visibility rules:
        - Approved events are visible to everyone
        - Unapproved events are only visible to their creator and admins
        - Admin users can see all events
        """
        user = self.request.user
        queryset = Event.objects.all()
        
        # For unauthenticated users, only show approved events
        if not user.is_authenticated:
            return queryset.filter(is_approved=True)
            
        # For admin users, show all events
        if user.is_staff:
            return queryset
            
        # For regular authenticated users, show approved events + their own unapproved events
        return queryset.filter(Q(is_approved=True) | Q(created_by=user))
    
    def perform_create(self, serializer):
        # Set the created_by user to the current user
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an event (admin only)"""
        event = self.get_object()
        event.is_approved = True
        event.save()
        return Response({'status': 'event approved'})
    
    @action(detail=True, methods=['post'])
    def unapprove(self, request, pk=None):
        """Unapprove an event (admin only)"""
        event = self.get_object()
        event.is_approved = False
        event.save()
        return Response({'status': 'event unapproved'})


class EventPhotoViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows event photos to be managed.
    """
    serializer_class = EventPhotoSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """
        Return photos for a specific event.
        Only show approved photos to non-owners and non-admins.
        """
        # Get the event_id from the URL parameters
        event_id = self.kwargs.get('event_pk')
        if not event_id:
            return EventPhoto.objects.none()
            
        try:
            event = Event.objects.get(id=event_id)
            queryset = EventPhoto.objects.filter(event=event)
            user = self.request.user
            
            # For unauthenticated users or non-owners, only show approved photos
            if not user.is_authenticated or (user != event.created_by and not getattr(user, 'is_staff', False)):
                queryset = queryset.filter(is_approved=True)
                
            return queryset.order_by('-uploaded_at')
            
        except Event.DoesNotExist:
            return EventPhoto.objects.none()
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsApprovedUser]
        elif self.action in ['approve', 'unapprove']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Set the event and uploaded_by user when creating a photo."""
        event_id = self.kwargs.get('event_pk')
        if not event_id:
            raise serializers.ValidationError("Event ID is required")
            
        try:
            event = Event.objects.get(id=event_id)
            # Set the event on the instance before saving
            instance = serializer.save(
                event=event,
                uploaded_by=self.request.user,
                is_approved=getattr(self.request.user, 'is_staff', False)  # Auto-approve for staff
            )
            
            # Update the filename to include the event ID
            if hasattr(instance, 'image') and instance.image:
                old_path = instance.image.path
                new_filename = f"event_{event_id}_{os.path.basename(instance.image.name)}"
                new_path = os.path.join(os.path.dirname(old_path), new_filename)
                
                # Rename the file
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                
                # Update the instance with the new path
                instance.image.name = os.path.join(os.path.dirname(instance.image.name), new_filename)
                instance.save(update_fields=['image'])
                
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event not found")
        except Exception as e:
            raise serializers.ValidationError(f"Error processing image: {str(e)}")
    
    @action(detail=True, methods=['post'])
    def approve(self, request, event_id=None, pk=None):
        """Approve a photo (admin only)"""
        photo = self.get_object()
        photo.is_approved = True
        photo.save()
        return Response({'status': 'photo approved'})
    
    @action(detail=True, methods=['post'])
    def unapprove(self, request, event_id=None, pk=None):
        """Unapprove a photo (admin only)"""
        photo = self.get_object()
        photo.is_approved = False
        photo.save()
        return Response({'status': 'photo unapproved'})
