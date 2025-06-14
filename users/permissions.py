from rest_framework import permissions


class IsApprovedOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow approved users to add or modify content.
    Read permissions are allowed to any request.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed if the user is authenticated and approved
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.is_approved
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to add or modify content.
    Read permissions are allowed to any request.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit or delete it.
    Read permissions are allowed to any request.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to the owner of the object
        return obj.created_by == request.user


class IsApprovedUser(permissions.BasePermission):
    """
    Custom permission to only allow approved users to access the view.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_approved or request.user.is_staff)
        )
