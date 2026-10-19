"""FR-13/FR-14: synthetic API routes exercise the configured handler."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, connection
from django.http import Http404
from django.test import SimpleTestCase, TransactionTestCase, override_settings
from django.urls import path
from rest_framework import exceptions, serializers
from rest_framework.authentication import BaseAuthentication
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.views import APIView

from common.exceptions import Conflict


class PublicView(APIView):
    authentication_classes = []
    permission_classes = []
    renderer_classes = [JSONRenderer]
    parser_classes = [JSONParser]


class InputSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=4)
    count = serializers.IntegerField(min_value=1, max_value=5)

    def validate(self, attrs):
        if attrs["label"] == "same":
            raise serializers.ValidationError("Choose a different label.")
        return attrs


class InputView(PublicView):
    def post(self, request):
        serializer = InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=201)


class NestedView(PublicView):
    def post(self, request):
        serializer = InputSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class ChallengeAuthentication(BaseAuthentication):
    """Test double only; US-01 owns the production authentication mechanism."""

    def authenticate(self, request):
        if request.headers.get("Authorization"):
            raise exceptions.AuthenticationFailed("private credential details")
        return None

    def authenticate_header(self, request):
        return "Bearer"


class ProtectedView(PublicView):
    authentication_classes = [ChallengeAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"ok": True})


class NoChallengeAuthentication(ChallengeAuthentication):
    def authenticate_header(self, request):
        return None


class SessionStyleView(ProtectedView):
    authentication_classes = [NoChallengeAuthentication]


class FailureView(PublicView):
    def get(self, request, kind):
        failures = {
            "missing": Http404("private lookup details"),
            "denied": PermissionDenied("private policy details"),
            "conflict": Conflict("The selected slot is already occupied."),
            "default-conflict": Conflict(),
            "crash": RuntimeError("password=secret SELECT * FROM private_table"),
            "integrity": IntegrityError("private database constraint"),
            "server": exceptions.APIException("private upstream failure"),
            "throttled": exceptions.Throttled(wait=12),
            "validation": serializers.ValidationError("Invalid combination."),
        }
        raise failures[kind]


class RollbackView(PublicView):
    def post(self, request, kind):
        get_user_model().objects.create(username="rollback-test-only")
        if kind == "conflict":
            raise Conflict()
        if kind == "validation":
            raise serializers.ValidationError({"label": ["Invalid."]})
        raise RuntimeError("private database failure")


# These URLs are loaded only through override_settings, never config.urls.
urlpatterns = [
    path("input/", InputView.as_view()),
    path("nested/", NestedView.as_view()),
    path("protected/", ProtectedView.as_view()),
    path("session-style/", SessionStyleView.as_view()),
    path("failure/<str:kind>/", FailureView.as_view()),
    path("rollback/<str:kind>/", RollbackView.as_view()),
]


@override_settings(ROOT_URLCONF=__name__)
class ErrorContractTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def assert_error(self, response, status, code):
        self.assertEqual(response.status_code, status)
        data = response.json()
        self.assertEqual(set(data), {"error", "code", "details"})
        self.assertEqual(data["code"], code)
        self.assertIsInstance(data["error"], str)
        self.assertTrue(data["error"])
        return data

    def test_missing_fields(self):
        data = self.assert_error(
            self.client.post("/input/", {}, format="json"), 400, "VALIDATION_ERROR"
        )
        self.assertEqual(set(data["details"]), {"label", "count"})

    def test_invalid_type(self):
        data = self.assert_error(
            self.client.post("/input/", {"label": "ok", "count": "bad"}, format="json"),
            400, "VALIDATION_ERROR",
        )
        self.assertIn("count", data["details"])

    def test_boundary_violations(self):
        for payload, field in [
            ({"label": "longer", "count": 1}, "label"),
            ({"label": "ok", "count": 0}, "count"),
            ({"label": "ok", "count": 6}, "count"),
        ]:
            with self.subTest(payload=payload):
                data = self.assert_error(
                    self.client.post("/input/", payload, format="json"),
                    400, "VALIDATION_ERROR",
                )
                self.assertIn(field, data["details"])

    def test_non_field_validation(self):
        data = self.assert_error(
            self.client.post("/input/", {"label": "same", "count": 1}, format="json"),
            400, "VALIDATION_ERROR",
        )
        self.assertEqual(data["details"]["non_field_errors"], ["Choose a different label."])

    def test_list_validation(self):
        data = self.assert_error(
            self.client.get("/failure/validation/"),
            400, "VALIDATION_ERROR",
        )
        self.assertEqual(data["details"], ["Invalid combination."])

    def test_nested_list_validation(self):
        data = self.assert_error(
            self.client.post("/nested/", [{"label": "ok", "count": 1}, {}], format="json"),
            400, "VALIDATION_ERROR",
        )
        # DRF supports list-shaped and index-keyed collection errors.
        details = data["details"]
        invalid_row = details[1] if isinstance(details, list) else details["1"]
        self.assertIn("label", invalid_row)
        self.assertIn("count", invalid_row)

    def test_malformed_json_is_safe(self):
        data = self.assert_error(
            self.client.post("/input/", '{"password": "secret",', content_type="application/json"),
            400, "PARSE_ERROR",
        )
        self.assertEqual(data["details"], {})
        self.assertNotIn("secret", str(data))

    def test_unauthenticated_preserves_challenge(self):
        response = self.client.get("/protected/")
        self.assert_error(response, 401, "AUTHENTICATION_REQUIRED")
        self.assertEqual(response["WWW-Authenticate"], "Bearer")

    def test_invalid_credentials_are_safe(self):
        data = self.assert_error(
            self.client.get("/protected/", HTTP_AUTHORIZATION="Bearer invalid"),
            401, "AUTHENTICATION_FAILED",
        )
        self.assertNotIn("private", str(data))

    def test_no_challenge_preserves_drf_403(self):
        self.assert_error(self.client.get("/session-style/"), 403, "AUTHENTICATION_REQUIRED")

    def test_permission_denied_is_safe(self):
        data = self.assert_error(self.client.get("/failure/denied/"), 403, "PERMISSION_DENIED")
        self.assertNotIn("private", str(data))

    def test_missing_resource_is_safe(self):
        data = self.assert_error(self.client.get("/failure/missing/"), 404, "NOT_FOUND")
        self.assertEqual(data["details"], {})
        self.assertNotIn("private", str(data))

    def test_conflict_has_public_message(self):
        data = self.assert_error(self.client.get("/failure/conflict/"), 409, "CONFLICT")
        self.assertEqual(data["error"], "The selected slot is already occupied.")
        self.assertEqual(data["details"], {})

    def test_default_conflict(self):
        self.assert_error(self.client.get("/failure/default-conflict/"), 409, "CONFLICT")

    def test_method_not_allowed_preserves_allow_header(self):
        response = self.client.get("/input/")
        self.assert_error(response, 405, "METHOD_NOT_ALLOWED")
        self.assertIn("POST", response["Allow"])

    def test_unsupported_media_type(self):
        self.assert_error(
            self.client.post("/input/", "plain text", content_type="text/plain"),
            415, "UNSUPPORTED_MEDIA_TYPE",
        )

    def test_unacceptable_response_format(self):
        self.assert_error(
            self.client.get("/input/", HTTP_ACCEPT="application/xml"),
            406, "NOT_ACCEPTABLE",
        )

    def test_throttle_preserves_retry_after(self):
        response = self.client.get("/failure/throttled/")
        self.assert_error(response, 429, "THROTTLED")
        self.assertEqual(response["Retry-After"], "12")

    def test_unexpected_failures_are_safe_in_both_debug_modes(self):
        for debug in (True, False):
            for kind in ("crash", "integrity", "server"):
                with self.subTest(debug=debug, kind=kind), override_settings(DEBUG=debug):
                    with self.assertLogs("common.exceptions", level="ERROR") as logs:
                        data = self.assert_error(
                            self.client.get(f"/failure/{kind}/"), 500, "INTERNAL_ERROR"
                        )
                    self.assertEqual(data["details"], {})
                    for secret in ("secret", "password", "SELECT", "private"):
                        self.assertNotIn(secret, str(data))
                        self.assertNotIn(secret, " ".join(logs.output))
                    self.assertIsNone(logs.records[0].exc_info)

    def test_success_and_valid_boundaries_are_unchanged(self):
        for count in (1, 5):
            with self.subTest(count=count):
                payload = {"label": "okay", "count": count}
                response = self.client.post("/input/", payload, format="json")
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.json(), payload)


@override_settings(ROOT_URLCONF=__name__)
class ErrorRollbackTests(TransactionTestCase):
    def test_failed_requests_roll_back_writes(self):
        for kind, status in (("validation", 400), ("conflict", 409), ("crash", 500)):
            with self.subTest(kind=kind), patch.dict(
                connection.settings_dict, {"ATOMIC_REQUESTS": True}
            ):
                with patch("common.exceptions.logger.error"):
                    response = APIClient().post(f"/rollback/{kind}/", {}, format="json")
                self.assertEqual(response.status_code, status)
                self.assertFalse(
                    get_user_model().objects.filter(username="rollback-test-only").exists()
                )
