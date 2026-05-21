import typing as t
from functools import wraps

from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response

from common.helper.constants import StatusCodes


def validate_request(serializer_class: t.Type[serializers.Serializer]) -> t.Callable:
    """
    Validates the incoming request body + query params using the given serializer.
    Injects the validated data as an extra positional argument after `request`.
    URL kwargs are merged into the validation data so path params can be validated,
    and are also forwarded to the view method as keyword arguments.
    """

    def decorator(func: t.Callable) -> t.Callable:
        @wraps(func)
        def wrapper(self, req: Request, *args, **kwargs):
            query_params = {key: req.query_params[key] for key in req.query_params}
            merged = {**req.data, **query_params, **kwargs}
            serialized = serializer_class(data=merged)

            if not serialized.is_valid():
                errors = [
                    {'field': field, 'message': str(messages[0])}
                    for field, messages in serialized.errors.items()
                ]
                return Response(
                    {
                        'success': False,
                        'code': StatusCodes().UNPROCESSABLE_ENTITY,
                        'message': 'Validation Failed',
                        'errors': errors,
                    },
                    status=StatusCodes().UNPROCESSABLE_ENTITY,
                )

            return func(self, req, serialized.data, *args, **kwargs)

        return wrapper

    return decorator
