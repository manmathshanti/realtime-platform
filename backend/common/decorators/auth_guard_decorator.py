from functools import wraps
from rest_framework.response import Response
from rest_framework import status

from common.auth.jwt_service import JWTService


def auth_guard(require_auth: bool = True):
    """
    Decorator that extracts the JWT bearer token, verifies it, loads the user,
    and attaches request.jwt_user + request.membership for the current org.

    The org_slug is resolved from the URL kwargs ('org_slug') when present.
    """
    def decorator(func):
        @wraps(func)
        def inner(self, request, *args, **kwargs):
            from apps.accounts.models import User, OrganizationMembership

            auth_header = (
                request.headers.get('Authorization')
                or request.META.get('HTTP_AUTHORIZATION', '')
            )

            if not auth_header:
                if require_auth:
                    return Response(
                        {'success': False, 'code': 401, 'message': 'Authorization header missing'},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
                request.jwt_user = None
                request.membership = None
                return func(self, request, *args, **kwargs)

            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return Response(
                    {'success': False, 'code': 401, 'message': 'Invalid Authorization header format'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            token = parts[1]
            try:
                payload = JWTService().verify_token(token)
            except Exception as exc:
                return Response(
                    {'success': False, 'code': 401, 'message': str(exc)},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            if payload.get('type') != 'access':
                return Response(
                    {'success': False, 'code': 401, 'message': 'Access token required'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            user_uuid = payload.get('sub')
            user = User.objects.filter(uuid=user_uuid, is_active=True, deleted_at__isnull=True).first()
            if not user:
                return Response(
                    {'success': False, 'code': 401, 'message': 'User not found or inactive'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            request.jwt_user = user
            request.user = user

            # Attach org membership when org_slug is in URL
            org_slug = kwargs.get('org_slug') or request.headers.get('X-Org-Slug')
            if org_slug:
                membership = OrganizationMembership.objects.select_related('organization').filter(
                    user=user,
                    organization__slug=org_slug,
                    is_active=True,
                    organization__is_active=True,
                ).first()
                request.membership = membership
                request.org = membership.organization if membership else None
            else:
                # Fall back to first active membership
                membership = OrganizationMembership.objects.select_related('organization').filter(
                    user=user, is_active=True, organization__is_active=True
                ).first()
                request.membership = membership
                request.org = membership.organization if membership else None

            return func(self, request, *args, **kwargs)

        return inner
    return decorator


def require_role(minimum_role: str):
    """
    Decorator applied after @auth_guard — checks that request.membership has
    a role at or above minimum_role in the hierarchy.
    """
    from common.permissions import ROLE_HIERARCHY

    def decorator(func):
        @wraps(func)
        def inner(self, request, *args, **kwargs):
            membership = getattr(request, 'membership', None)
            if not membership:
                return Response(
                    {'success': False, 'code': 403, 'message': 'Organization membership required'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            user_level = ROLE_HIERARCHY.get(membership.role, 0)
            required_level = ROLE_HIERARCHY.get(minimum_role, 0)
            if user_level < required_level:
                return Response(
                    {'success': False, 'code': 403, 'message': 'Insufficient permissions'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            return func(self, request, *args, **kwargs)
        return inner
    return decorator
