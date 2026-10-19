# Shared API errors (US-31)

Implements [US-31 / issue #51](https://github.com/Vehicle-Parking-System-Team/Vehicle-Parking-System-SE-MINI-PROJECT/issues/51), FR-13 (backend validation) and FR-14 (meaningful errors). Use this top-level format for errors raised from DRF endpoints:

```json
{
  "error": "Please correct the highlighted fields.",
  "code": "VALIDATION_ERROR",
  "details": {
    "registration_number": ["This field is required."]
  }
}
```

- `error`: a safe, non-empty message for display.
- `code`: a stable uppercase machine-readable string. Clients must not branch on message wording.
- `details`: serializer validation details, preserving nested objects, lists and collection indices. Non-field errors can be a root list or `non_field_errors`. For other errors, this is `{}`.
- Success payloads and HTTP statuses are unchanged. Request JSON with `Accept: application/json`.

## Status and code mapping

| Condition | HTTP | Code |
| --- | --- | --- |
| Serializer validation | 400 | `VALIDATION_ERROR` |
| Malformed body | 400 | `PARSE_ERROR` |
| Other handled bad request | 400 | `BAD_REQUEST` |
| Missing authentication | 401* | `AUTHENTICATION_REQUIRED` |
| Invalid authentication | 401* | `AUTHENTICATION_FAILED` |
| Permission denied | 403 | `PERMISSION_DENIED` |
| Resource lookup fails | 404 | `NOT_FOUND` |
| Unsupported method | 405 | `METHOD_NOT_ALLOWED` |
| Unsupported response format | 406 | `NOT_ACCEPTABLE` |
| Explicit domain conflict | 409 | `CONFLICT` |
| Unsupported request content type | 415 | `UNSUPPORTED_MEDIA_TYPE` |
| Throttling | 429 | `THROTTLED` |
| Unexpected exception | 500 | `INTERNAL_ERROR` |
| Explicit server-side API exception | Original 5xx | `INTERNAL_ERROR` |
| Other custom client-side API exception | Original status | `API_ERROR` |

*DRF uses 403 for authentication failures when the configured authenticator does not provide a challenge. The handler preserves that behavior and any `WWW-Authenticate`, `Retry-After` and `Allow` headers. Authentication implementation remains owned by US-01.

## Backend usage

`config.settings.REST_FRAMEWORK.EXCEPTION_HANDLER` points to `common.exceptions.exception_handler`; individual DRF views do not need to wrap exceptions.

```python
from common.exceptions import Conflict

serializer.is_valid(raise_exception=True)
if expected_business_conflict:
    raise Conflict("The selected slot is already occupied.")
```

Use DRF serializers for domain-specific missing/format/boundary checks. Raise `Http404`/DRF `NotFound` for unknown resources and the existing permission exceptions for denied access. Raise exceptions rather than returning ad hoc `Response(..., status=400)` bodies, which bypass the exception handler.

Only supply public-safe validation and conflict messages. Never interpolate passwords, tokens, raw SQL or internal exception text. Other exception messages are replaced with generic text. Raw database integrity failures remain internal errors; owners must recognize expected conflicts in their own services rather than relabel every database failure as 409.

### Server-side debugging policy

Unexpected failures log a sanitized traceback through `common.exceptions` at ERROR level. It retains the originating view, exception and cause/context types, and each stack frame's module, function, filename and line number. This provides failure locations and call-chain context while the API continues to return the generic `INTERNAL_ERROR` envelope with empty `details`, including when DEBUG is enabled.

Exception messages, source-code lines, local variables, request bodies, headers, URLs and query parameters are excluded from these diagnostic records. The logger receives only the sanitized text, not raw `exc_info` or exception objects that another formatter/collector might serialize. Exception chains respect suppressed context and terminate on cycles. This is an allowlist of diagnostic metadata, not a regex-based attempt to identify every possible secret.

Treat backend log destinations as operational data: production handlers/collectors must restrict access to authorized maintainers and apply the deployment's retention policy. This repository does not provision or verify a production log store. Do not expose these logs through application endpoints or enable raw exception/request capture in a collector without an independently reviewed redaction policy. Other application logging remains the responsibility of its owner.

The handler preserves DRF's rollback marking for handled exceptions and also marks unexpected failures for rollback under `ATOMIC_REQUESTS`. Domain owners still own transaction boundaries, database constraints and concurrent-operation correctness. A shared error handler does not make non-transactional writes atomic.

## Frontend usage

`parseApiError` in `frontend/src/utils/apiErrors.js` accepts an already parsed JSON body and returns `{ message, code, fieldErrors, formErrors }`.

```javascript
import { parseApiError } from './utils/apiErrors.js'

// Inside the form's existing request handler:
const body = await response.json().catch(() => null)
if (!response.ok) {
  setApiError(parseApiError(body))
  return
}
```

For a network failure, pass `null` to obtain a safe general fallback. Display `message` in the form's alert area, `formErrors` as general validation messages, and `fieldErrors.registration_number` beside that field. Nested fields use dotted paths, such as `vehicles.0.registration_number`. Both DRF list and index-keyed collection errors are supported. Render messages as React text; do not inject them as HTML. The helper does not mutate the response or manage fetching, authentication or page state.

## Integration boundaries

This contract applies to exceptions handled inside DRF's request lifecycle. Django admin pages, unmatched URL routes, middleware/proxy errors and failures during response rendering are outside that lifecycle; the frontend helper safely falls back on unstructured/non-JSON bodies. Existing content negotiation, permissions and endpoint paths are retained.

Each module owner should use serializer exceptions and `Conflict` in their own story and verify the envelope on real endpoints. No domain models, migrations, authentication policy or demonstration production routes are introduced by US-31. Test-only routes are isolated from `config.urls`.

See [test cases and execution evidence](../testing/US31-test-evidence.md).
