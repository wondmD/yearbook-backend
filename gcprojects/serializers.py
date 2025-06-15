from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = fields

class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for the Project model."""
    user = UserSerializer(read_only=True, required=False)
    technologies = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'code_url', 'live_url',
            'image_url', 'technologies', 'is_featured',
            'created_at', 'updated_at', 'user'
        ]
        read_only_fields = ['created_at', 'updated_at', 'user']
    
    def validate_title(self, value):
        """Validate that the title is unique."""
        if Project.objects.filter(title=value).exists():
            raise serializers.ValidationError("A project with this title already exists.")
        return value
    
    def validate_urls(self, data):
        """Validate that at least one URL (code or live) is provided."""
        if not data.get('code_url') and not data.get('live_url'):
            raise serializers.ValidationError(
                "At least one of code_url or live_url must be provided."
            )
        return data
    
    def to_representation(self, instance):
        """Customize the representation of the project."""
        representation = super().to_representation(instance)
        
        # Add a computed field for the full name
        if instance.user:
            representation['user_full_name'] = f"{instance.user.first_name} {instance.user.last_name}".strip()
        else:
            representation['user_full_name'] = None
            
        return representation 