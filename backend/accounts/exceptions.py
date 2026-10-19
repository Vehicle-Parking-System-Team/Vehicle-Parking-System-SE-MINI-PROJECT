"""US-31 error contract exception handler for accounts and authentication."""

from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


_ERRORS = {
    400: ('BAD_REQUEST', 'The request could not be processed.'),
    401: ('AUTHENTICATION_REQUIRED', 'Authentication is required.'),
    403: ('PERMISSION_DENIED', 'You do not have permission to perform this action.'),
    404: ('NOT_FOUND', 'The requested resource was not found.'),
    405: ('METHOD_NOT_ALLOWED', 'This request method is not allowed.'),
    429: ('THROTTLED', 'Too many requests. Please try again later.'),
}


def exception_handler(exc, context):
    """
    Standardize exception responses into the US-31 envelope:
    {'error': ..., 'code': ..., 'details': ...}
    """
    response = drf_exception_handler(exc, context)

    if response is None:
        return Response(
            {
                'error': 'An unexpected error occurred.',
                'code': 'INTERNAL_ERROR',
                'details': {},
            },
            status=500,
        )

    code = 'REQUEST_FAILED'
    details = {}
    message = 'The request could not be processed.'

    if isinstance(exc, exceptions.ValidationError):
        code = 'VALIDATION_ERROR'
        message = 'Validation failed.'
        details = response.data
    elif isinstance(exc, exceptions.AuthenticationFailed):
        code = 'AUTHENTICATION_FAILED'
        # Provide clean, generic message to client without leaking user existence or internal tokens
        message = str(exc.detail) if isinstance(exc.detail, str) else 'Authentication failed.'
    elif isinstance(exc, exceptions.NotAuthenticated):
        code = 'AUTHENTICATION_REQUIRED'
        message = 'Authentication is required.'
    elif response.status_code in _ERRORS:
        code, message = _ERRORS[response.status_code]
        if hasattr(exc, 'detail') and isinstance(exc.detail, str):
            message = str(exc.detail)
    elif response.status_code >= 500:
        code = 'INTERNAL_ERROR'
        message = 'An unexpected error occurred.'

    response.data = {
        'error': message,
        'code': code,
        'details': details,
    }
    return response
