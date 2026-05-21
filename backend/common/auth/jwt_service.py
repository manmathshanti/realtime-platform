from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from django.conf import settings

from common.exceptions import UnauthorizedException


class JWTService:
    """Creates and verifies JWT access and refresh tokens."""

    _secret: str = None
    _algorithm: str = None

    @classmethod
    def _get_secret(cls) -> str:
        if cls._secret is None:
            cls._secret = settings.JWT_SECRET
        return cls._secret

    @classmethod
    def _get_algorithm(cls) -> str:
        if cls._algorithm is None:
            cls._algorithm = settings.JWT_ALGORITHM
        return cls._algorithm

    def create_access_token(self, user_id: str) -> str:
        exp_minutes = getattr(settings, 'JWT_ACCESS_EXP_MINUTES', 60)
        now = datetime.now(timezone.utc)
        payload = {
            'sub': str(user_id),
            'type': 'access',
            'iat': now,
            'exp': now + timedelta(minutes=exp_minutes),
        }
        return jwt.encode(payload, self._get_secret(), algorithm=self._get_algorithm())

    def create_refresh_token(self, user_id: str) -> str:
        exp_days = getattr(settings, 'JWT_REFRESH_EXP_DAYS', 30)
        now = datetime.now(timezone.utc)
        payload = {
            'sub': str(user_id),
            'type': 'refresh',
            'iat': now,
            'exp': now + timedelta(days=exp_days),
        }
        return jwt.encode(payload, self._get_secret(), algorithm=self._get_algorithm())

    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self._get_secret(), algorithms=[self._get_algorithm()])
            return payload
        except JWTError as exc:
            raise UnauthorizedException(f'Invalid or expired token: {exc}')
