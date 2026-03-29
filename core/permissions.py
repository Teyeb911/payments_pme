from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Accès réservé aux administrateurs."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsCommerçant(BasePermission):
    """Accès réservé aux commerçants."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'commercant'
        )


class IsOwnerOrAdmin(BasePermission):
    """Propriétaire de l'objet ou admin."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        owner = getattr(obj, 'commercant', None)
        return owner == request.user


class IsAdminOrReadOnly(BasePermission):
    """Admin en écriture, lecture publique."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'admin'
