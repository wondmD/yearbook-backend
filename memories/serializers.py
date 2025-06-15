from rest_framework import serializers
from .models import Memory
from django.conf import settings

class MemorySerializer(serializers.ModelSerializer):
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    created_by_avatar = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Memory
        fields = [
            'id', 'title', 'description', 'image', 'image_url', 
            'created_by', 'created_by_username', 'created_by_avatar',
            'created_at', 'is_approved', 'likes_count', 'has_liked'
        ]
        read_only_fields = ['created_by', 'is_approved']

    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

    def get_created_by_avatar(self, obj):
        # Safely get the avatar URL if it exists
        if hasattr(obj.created_by, 'avatar') and obj.created_by.avatar:
            try:
                return self.context['request'].build_absolute_uri(obj.created_by.avatar.url)
            except (ValueError, AttributeError):
                # Handle case where avatar doesn't have a file or URL is invalid
                pass
        return None

    def get_likes_count(self, obj):
        # Use the correct field name for likes count
        if hasattr(obj, 'likes_count'):
            return obj.likes_count
        # Fallback to counting the related likes
        return obj.likes.count() if hasattr(obj, 'likes') else 0

    def get_has_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
