from rest_framework.permissions import BasePermission


ROLE_HIERARCHY = {
    'owner': 4,
    'admin': 3,
    'analyst': 2,
    'viewer': 1,
}


def _get_role_level(role: str) -> int:
    return ROLE_HIERARCHY.get(role, 0)


class IsAuthenticated(BasePermission):
    """Request must have a valid JWT user attached by auth_guard."""

    def has_permission(self, request, view):
        return hasattr(request, 'jwt_user') and request.jwt_user is not None


class IsOrganizationMember(BasePermission):
    """User must belong to the organization in request.org."""

    def has_permission(self, request, view):
        return (
            hasattr(request, 'jwt_user')
            and request.jwt_user is not None
            and hasattr(request, 'membership')
            and request.membership is not None
        )


class IsAnalystOrAbove(BasePermission):
    def has_permission(self, request, view):
        membership = getattr(request, 'membership', None)
        if not membership:
            return False
        return _get_role_level(membership.role) >= _get_role_level('analyst')


class IsAdminOrAbove(BasePermission):
    def has_permission(self, request, view):
        membership = getattr(request, 'membership', None)
        if not membership:
            return False
        return _get_role_level(membership.role) >= _get_role_level('admin')


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        membership = getattr(request, 'membership', None)
        if not membership:
            return False
        return membership.role == 'owner'
