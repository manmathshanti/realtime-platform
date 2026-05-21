from rest_framework.views import APIView
from rest_framework.response import Response

from common.helper.constants import StatusCodes

class BaseAPIView(APIView):
    """
    Base class for API views that includes standard methods for handling
    responses such as success, error, validation failure, etc.
    """

    def success(self, data, code=StatusCodes().SUCCESS, msg=None):
        """Returns a success response with the provided data and message."""
        return Response(
            {
                "success": True,
                "code": code,
                "data": data,
                "message": msg or "Request was successful."
            },
            status=code,
        )

    def error(self, errors, status_code):
        """Returns an error response with the given error details and status code."""
        return Response(
            {
                "success": False,
                "code": status_code,
                "errors": errors,
                "message": errors,
            },
            status=status_code,
        )

    def validation_failed(self, errors):
        """Returns a validation failure response."""
        return self.error(errors, StatusCodes().UNPROCESSABLE_ENTITY)

    def error_message(self, msg, code, data=None):
        """Returns an error message response with the given status code and data."""
        return Response(
            {"success": False, "code": code, "message": msg, "data": data}, status=code
        )

    def error_message_without_data(self, msg, code):
        """Returns an error message response without any additional data."""
        return Response(
            {"success": False, "code": code, "message": msg}, status=code
        )

    def no_content(self):
        """Returns a no content (204) response."""
        return Response(status=StatusCodes().NO_CONTENT)
