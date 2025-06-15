from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import permission_classes
from .models import Memory
from .serializers import MemorySerializer

class PendingMemoriesView(APIView):
    """
    API endpoint to get all unapproved memories for admin review
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()
    
    def get(self, request):
        """
        Get all unapproved memories
        """
        try:
            memories = Memory.objects.filter(is_approved=False).select_related('created_by')
            serializer = MemorySerializer(memories, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, memory_id=None):
        """
        Approve or reject a memory
        """
        if not memory_id:
            return Response(
                {'error': 'Memory ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            memory = Memory.objects.get(id=memory_id)
            action = request.data.get('action', '').lower()
            
            if action == 'approve':
                memory.is_approved = True
                memory.save()
                return Response(
                    {'status': 'approved', 'message': 'Memory approved successfully'},
                    status=status.HTTP_200_OK
                )
            elif action == 'reject':
                memory_id = memory.id  # Save the ID before deletion for the response
                memory.delete()
                return Response(
                    {'status': 'rejected', 'message': 'Memory rejected and deleted', 'id': memory_id},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Invalid action. Must be "approve" or "reject"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Memory.DoesNotExist:
            return Response(
                {'error': 'Memory not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
