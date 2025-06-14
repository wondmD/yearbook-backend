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
