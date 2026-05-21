import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception with a status code and message."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = 'An unexpected error occurred.'

    def __init__(self, message: str = None, status_code: int = None):
        self.message = message or self.default_message
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = 'Resource not found.'


class ForbiddenException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = 'You do not have permission to perform this action.'


class UnauthorizedException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = 'Authentication credentials were not provided or are invalid.'


class ValidationException(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_message = 'Validation failed.'


class ConflictException(AppException):
    status_code = status.HTTP_409_CONFLICT
    default_message = 'Resource already exists.'


class RateLimitException(AppException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_message = 'Rate limit exceeded.'


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, AppException):
        return Response(
            {
                'success': False,
                'code': exc.status_code,
                'message': exc.message,
            },
            status=exc.status_code,
        )

    if response is not None:
        response.data = {
            'success': False,
            'code': response.status_code,
            'message': _extract_message(response.data),
            'errors': response.data if isinstance(response.data, dict) else None,
        }
        return response

    logger.exception('Unhandled exception', exc_info=exc)
    return Response(
        {
            'success': False,
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'message': 'An internal server error occurred.',
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _extract_message(data) -> str:
    if isinstance(data, dict):
        for key in ('detail', 'message', 'non_field_errors'):
            if key in data:
                val = data[key]
                return str(val[0]) if isinstance(val, list) else str(val)
        first_val = next(iter(data.values()), None)
        if first_val:
            return str(first_val[0]) if isinstance(first_val, list) else str(first_val)
    if isinstance(data, list) and data:
        return str(data[0])
    return str(data)
