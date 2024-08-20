from rest_framework.permissions import BasePermission
class IsAuthenticatedCustom(BasePermission):
    """
    Custom permission class that checks if the user is authenticated.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
