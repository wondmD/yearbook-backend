from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .models import Event, EventPhoto
from .serializers import EventSerializer, EventPhotoSerializer

class PendingEventsView(APIView):
    """
    API endpoint to get all unapproved events for admin review
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        events = Event.objects.filter(is_approved=False).select_related('created_by')
        serializer = EventSerializer(events, many=True, context={'request': request})
        return Response(serializer.data)
    
    def patch(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id)
            action = request.data.get('action')
            
            if action == 'approve':
                event.is_approved = True
                event.save()
                return Response(
                    {'status': 'approved', 'message': 'Event approved successfully'},
                    status=status.HTTP_200_OK
                )
            elif action == 'reject':
                event.delete()
                return Response(
                    {'status': 'rejected', 'message': 'Event rejected and deleted'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Invalid action'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Event.DoesNotExist:
            return Response(
                {'error': 'Event not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class PendingPhotosView(APIView):
    """
    API endpoint to get all unapproved photos for admin review
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        photos = EventPhoto.objects.filter(is_approved=False).select_related('event', 'uploaded_by')
        serializer = EventPhotoSerializer(photos, many=True, context={'request': request})
        return Response(serializer.data)
    
    def patch(self, request, photo_id):
        try:
            photo = EventPhoto.objects.get(id=photo_id)
            action = request.data.get('action')
            
            if action == 'approve':
                photo.is_approved = True
                photo.save()
                return Response(
                    {'status': 'approved', 'message': 'Photo approved successfully'},
                    status=status.HTTP_200_OK
                )
            elif action == 'reject':
                photo.delete()
                return Response(
                    {'status': 'rejected', 'message': 'Photo rejected and deleted'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Invalid action'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except EventPhoto.DoesNotExist:
            return Response(
                {'error': 'Photo not found'},
                status=status.HTTP_404_NOT_FOUND
            )
