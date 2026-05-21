from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def get_user_from_token(token: str):
    """Validates JWT token and returns the User (or None)."""
    try:
        from common.auth.jwt_service import JWTService
        from apps.accounts.models import User
        payload = JWTService().verify_token(token)
        if payload.get('type') != 'access':
            return None
        return User.objects.filter(uuid=payload['sub'], is_active=True).first()
    except Exception:
        return None


class JWTAuthMiddleware(BaseMiddleware):
    """
    WebSocket middleware that authenticates via:
    1. Query string:  ?token=<access_token>
    2. Subprotocol:   Authorization header (some WS clients)
    Attaches scope['user'] so consumers can check authentication.
    """

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        token = None

        token_list = params.get('token', [])
        if token_list:
            token = token_list[0]

        if not token:
            # Try subprotocols (Bearer token passed as subprotocol)
            for header_name, header_value in scope.get('headers', []):
                if header_name == b'authorization':
                    parts = header_value.decode().split()
                    if len(parts) == 2 and parts[0].lower() == 'bearer':
                        token = parts[1]
                    break

        scope['user'] = await get_user_from_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)
