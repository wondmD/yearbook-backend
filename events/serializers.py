from rest_framework import serializers
from .models import Event, EventPhoto
from users.serializers import UserSerializer

class EventPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = EventPhoto
        fields = [
            'id',
            'image',
            'image_url',
            'caption',
            'uploaded_by',
            'uploaded_at',
            'is_approved'
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at', 'is_approved']
    
    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

class EventSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    photos = EventPhotoSerializer(many=True, read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id',
            'slug',
            'title',
            'date',
            'location',
            'description',
            'attendees_count',
            'photos_count',
            'highlights',
            'category',
            'category_display',
            'cover_image',
            'cover_image_url',
            'created_by',
            'created_at',
            'updated_at',
            'is_approved',
            'photos',  # Nested photos
        ]
        read_only_fields = ['slug', 'created_by', 'created_at', 'updated_at', 'photos_count', 'is_approved']
    
    def get_cover_image_url(self, obj):
        if obj.cover_image:
            return self.context['request'].build_absolute_uri(obj.cover_image.url)
        return None
    
    def create(self, validated_data):
        # Set the created_by user from the request
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class EventCreateSerializer(EventSerializer):
    """Serializer for creating events with additional validation"""
    class Meta(EventSerializer.Meta):
        fields = EventSerializer.Meta.fields
        read_only_fields = [f for f in EventSerializer.Meta.read_only_fields if f != 'is_approved']
    
    def validate_highlights(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Highlights must be a list of strings")
        if len(value) > 10:  # Limit number of highlights
            raise serializers.ValidationError("Maximum 10 highlights allowed")
        return value
