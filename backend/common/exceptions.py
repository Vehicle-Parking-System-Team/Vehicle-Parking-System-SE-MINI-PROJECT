"""The US-31 error contract for DRF views and services."""

import logging

from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.views import set_rollback

logger = logging.getLogger(__name__)


class Conflict(exceptions.APIException):
    """Raise for an expected business conflict, using a safe public message."""

    status_code = 409
    default_detail = "The operation conflicts with the current state."
    default_code = "conflict"


_ERRORS = {
    400: ("BAD_REQUEST", "The request could not be processed."),
    401: ("AUTHENTICATION_REQUIRED", "Authentication is required."),
    403: ("PERMISSION_DENIED", "You do not have permission to perform this action."),
    404: ("NOT_FOUND", "The requested resource was not found."),
    405: ("METHOD_NOT_ALLOWED", "This request method is not allowed."),
    406: ("NOT_ACCEPTABLE", "The requested response format is not supported."),
    409: ("CONFLICT", str(Conflict.default_detail)),
    415: ("UNSUPPORTED_MEDIA_TYPE", "The request content type is not supported."),
    429: ("THROTTLED", "Too many requests. Please try again later."),
}


def exception_handler(exc, context):
    """Preserve DRF status/headers/rollback and return error, code and details."""
    response = drf_exception_handler(exc, context)
    if response is None:
        # A handled 500 must still roll back an ATOMIC_REQUESTS transaction.
        set_rollback()
        response = Response(status=500)

    details = {}
    if response.status_code >= 500:
        code, message = "INTERNAL_ERROR", "An unexpected error occurred."
        # Exception text, tracebacks, request data and URLs may contain secrets.
        logger.error("API failure (%s).", type(exc).__name__)
    elif isinstance(exc, exceptions.ValidationError):
        code, message = "VALIDATION_ERROR", "Please correct the highlighted fields."
        details = response.data
    elif isinstance(exc, exceptions.ParseError):
        code, message = "PARSE_ERROR", "The request body is malformed."
    elif isinstance(exc, exceptions.AuthenticationFailed):
        code, message = "AUTHENTICATION_FAILED", "Authentication failed."
    elif isinstance(exc, exceptions.NotAuthenticated):
        code, message = "AUTHENTICATION_REQUIRED", "Authentication is required."
    else:
        code, message = _ERRORS.get(
            response.status_code, ("API_ERROR", "The request could not be processed.")
        )
        if isinstance(exc, Conflict) and isinstance(exc.detail, str):
            message = str(exc.detail)

    response.data = {"error": message, "code": code, "details": details}
    return response
