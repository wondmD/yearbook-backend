from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the UserProfile model."""
    # User fields we want to include in the profile
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    is_approved = serializers.BooleanField(read_only=True)  # Now using the profile's is_approved field
    student_id = serializers.CharField(source='user.student_id', required=False)
    batch = serializers.CharField(source='user.batch', required=False)
    role = serializers.CharField(source='user.role', required=False)
    
    # Profile fields
    image = serializers.ImageField(required=False, allow_null=True)
    social_links = serializers.JSONField(required=False, default=dict)
    
    class Meta:
        model = UserProfile
        fields = [
            # User fields
            'username', 'email', 'first_name', 'last_name',
            'is_approved', 'student_id', 'batch', 'role',
            # Profile fields
            'id', 'nickname', 'bio', 'location', 'interests',
            'image', 'fun_fact', 'social_links', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'username', 'email', 'is_approved']
    
    def update(self, instance, validated_data):
        # Handle nested user data if present
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
            
        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Ensure is_approved is included from the profile model
        representation['is_approved'] = instance.is_approved
        
        if representation.get('image'):
            # Get the raw image path from the instance
            image_path = str(instance.image)
            
            # If it's already a URL, extract just the filename
            if 'http' in image_path:
                # Extract just the filename from the URL
                image_path = image_path.split('/')[-1]
            
            # Remove any leading /media/ or media/ if present
            image_path = image_path.replace('/media/', '').replace('media/', '')
            
            # Remove any duplicate profile_images/ prefixes
            while image_path.startswith('profile_images/'):
                image_path = image_path[15:]
            
            # Construct the correct relative path
            image_path = f"profile_images/{image_path}"
            
            # Always return just the relative path (frontend will handle the base URL)
            representation['image'] = f"/media/{image_path}"
            
            # If we have a request and need an absolute URL, construct it properly
            request = self.context.get('request')
            if request and request.build_absolute_uri().startswith(('http://', 'https://')):
                # Only use the host from the request, don't include /media/ again
                base_url = request.build_absolute_uri('/').rstrip('/')
                representation['image'] = f"{base_url}/media/{image_path}"
                
        return representation
    
    def to_internal_value(self, data):
        # Handle case where image is a URL string
        if 'image' in data and isinstance(data['image'], str):
            # If it's a URL, we'll handle it in the update method
            return super().to_internal_value(data)
        return super().to_internal_value(data)
    
    def update(self, instance, validated_data):
        # If image is a URL, don't try to update it (it's already set via the image endpoint)
        if 'image' in validated_data and isinstance(validated_data['image'], str):
            validated_data.pop('image')
        return super().update(instance, validated_data)

class UserSerializer(serializers.ModelSerializer): 
    """Serializer for the User model."""
    # Use string reference to avoid circular import
    profile = None  # Will be set after both serializers are defined
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'is_active', 'is_staff', 'is_superuser', 'date_joined',
                 'profile', 'password']
        read_only_fields = ['id', 'is_active', 'is_staff', 'is_superuser', 'date_joined']

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password', None)
        
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        
        # Create profile if data is provided
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
            
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
        instance.save()
        
        # Update or create profile
        if hasattr(instance, 'profile'):
            for attr, value in profile_data.items():
                setattr(instance.profile, attr, value)
            instance.profile.save()
        else:
            UserProfile.objects.create(user=instance, **profile_data)
            
        return instance

# Resolve circular imports after both classes are defined
UserProfileSerializer.user = UserSerializer(read_only=True)
UserSerializer.profile = UserProfileSerializer(required=False)

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_approved=False  # New users need admin approval
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
