from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

from .models import Display

class IsDisplayAuthenticated(BasePermission):
    def has_permission(self, request, view):
        if not hasattr(request, 'user') or not isinstance(request.user, Display):
            raise PermissionDenied("Authentication credentials were not provided.")
        return True