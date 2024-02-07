from rest_framework import permissions


class IsPartner(permissions.BasePermission):
    """The user is a partner."""

    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated and request.user.is_partner
        )
