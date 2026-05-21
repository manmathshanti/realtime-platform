import uuid
import time
import logging

logger = logging.getLogger(__name__)


class CorrelationIDMiddleware:
    """Attaches a correlation ID to every request for distributed tracing."""

    HEADER = 'X-Correlation-ID'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.headers.get(self.HEADER) or str(uuid.uuid4())
        request.correlation_id = correlation_id
        response = self.get_response(request)
        response[self.HEADER] = correlation_id
        return response


class RequestLoggingMiddleware:
    """Logs method, path, status code, and duration for every request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        correlation_id = getattr(request, 'correlation_id', '-')
        logger.info(
            '%s %s %s %sms [%s]',
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            correlation_id,
        )
        return response
