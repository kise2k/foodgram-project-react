from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrAdminOrReadOnly(BasePermission):
    """Права доступа для или автора или админа или только читать."""

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or obj.author == request.user)
