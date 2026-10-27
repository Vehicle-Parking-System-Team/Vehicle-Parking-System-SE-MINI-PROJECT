"""US-32 shared security configuration and existing boundary regressions."""

import os
import runpy
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from django.middleware.csrf import get_token
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import User
from vehicles.models import Vehicle


class SecurityConfigurationTests(SimpleTestCase):
    def load_settings(self, **environment):
        # Do not read developer .env files or mutate the running Django settings.
        with patch.dict(os.environ, environment, clear=True), patch('dotenv.load_dotenv'):
            return runpy.run_path(str(Path(settings.BASE_DIR) / 'config' / 'settings.py'))

    def test_signing_key_is_required_in_both_modes(self):
        for debug in ('True', 'False'):
            for key in ('', '   '):
                with self.subTest(debug=debug, key=key):
                    with self.assertRaisesMessage(ImproperlyConfigured, 'DJANGO_SECRET_KEY'):
                        self.load_settings(DJANGO_DEBUG=debug, DJANGO_SECRET_KEY=key)

    def test_environment_key_signs_jwt(self):
        key = get_random_secret_key()
        config = self.load_settings(DJANGO_SECRET_KEY=key)
        self.assertEqual(config['SECRET_KEY'], key)
        self.assertEqual(config['SIMPLE_JWT']['SIGNING_KEY'], key)

    def test_production_defaults_require_https_and_no_cross_origin_trust(self):
        config = self.load_settings(DJANGO_SECRET_KEY=get_random_secret_key(), DJANGO_DEBUG='False')
        for name in ('SECURE_SSL_REDIRECT', 'SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE'):
            self.assertTrue(config[name])
        self.assertEqual(config['CORS_ALLOWED_ORIGINS'], [])
        self.assertEqual(config['CSRF_TRUSTED_ORIGINS'], [])
        self.assertNotIn('SECURE_PROXY_SSL_HEADER', config)

    def test_development_retains_http_and_local_vite_origins(self):
        config = self.load_settings(DJANGO_SECRET_KEY=get_random_secret_key())
        for name in ('SECURE_SSL_REDIRECT', 'SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE'):
            self.assertFalse(config[name])
        self.assertEqual(config['CORS_ALLOWED_ORIGINS'], [
            'http://localhost:5173', 'http://127.0.0.1:5173',
        ])

    def test_cors_and_csrf_trust_are_configured_independently(self):
        config = self.load_settings(
            DJANGO_SECRET_KEY=get_random_secret_key(),
            CORS_ALLOWED_ORIGINS=' https://client.example, ',
            CSRF_TRUSTED_ORIGINS=' https://session.example, ',
        )
        self.assertEqual(config['CORS_ALLOWED_ORIGINS'], ['https://client.example'])
        self.assertEqual(config['CSRF_TRUSTED_ORIGINS'], ['https://session.example'])

    def test_postgres_requires_an_environment_password(self):
        with self.assertRaisesMessage(ImproperlyConfigured, 'DB_PASSWORD'):
            self.load_settings(
                DJANGO_SECRET_KEY=get_random_secret_key(), DB_ENGINE='django.db.backends.postgresql',
            )

    def test_postgres_uses_environment_password(self):
        password = get_random_secret_key()
        config = self.load_settings(
            DJANGO_SECRET_KEY=get_random_secret_key(), DB_ENGINE='django.db.backends.postgresql',
            DB_PASSWORD=password,
        )
        self.assertEqual(config['DATABASES']['default']['PASSWORD'], password)


@override_settings(
    CORS_ALLOWED_ORIGINS=['https://client.example'], CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOW_CREDENTIALS=False, CSRF_TRUSTED_ORIGINS=[], SECURE_SSL_REDIRECT=False,
)
class SecurityBoundaryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.operator = User.objects.create_user(username='security_operator', role='Operator')
        cls.customer = User.objects.create_user(username='security_customer', role='Customer')
        cls.vehicle = Vehicle.objects.create(
            owner=cls.operator, registration_number='KA-01-AB-1234', vehicle_type='Compact',
        )

    def test_allowed_cors_preflight_echoes_exact_origin(self):
        response = self.client.options(
            '/api/parking/slots/', HTTP_ORIGIN='https://client.example',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='authorization,content-type',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'https://client.example')
        self.assertNotIn('Access-Control-Allow-Credentials', response.headers)

    def test_untrusted_preflight_has_no_allow_origin(self):
        for origin in ('https://untrusted.example', 'https://client.example.untrusted.example', 'null'):
            with self.subTest(origin=origin):
                response = self.client.options(
                    '/api/parking/slots/', HTTP_ORIGIN=origin,
                    HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
                )
                self.assertNotIn('Access-Control-Allow-Origin', response.headers)

    def test_untrusted_origin_does_not_bypass_authentication(self):
        response = self.client.post('/api/parking/check-in/', {}, HTTP_ORIGIN='https://untrusted.example')
        self.assertEqual(response.status_code, 401)
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)

    def session_client(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.operator)
        return client

    def test_session_write_without_csrf_is_forbidden(self):
        response = self.session_client().post('/api/parking/check-in/', {}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_valid_csrf_reaches_payload_validation(self):
        client = self.session_client()
        request = RequestFactory().get('/')
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META['CSRF_COOKIE']
        response = client.post('/api/parking/check-in/', {}, format='json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 400)

    def test_cors_allowlist_does_not_grant_csrf_trust(self):
        client = self.session_client()
        request = RequestFactory().get('/')
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META['CSRF_COOKIE']
        response = client.post(
            '/api/parking/check-in/', {}, format='json', HTTP_X_CSRFTOKEN=token,
            HTTP_ORIGIN='https://client.example',
        )
        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_read_or_modify_another_vehicle(self):
        client = APIClient()
        client.force_authenticate(self.customer)
        url = f'/api/v1/vehicles/{self.vehicle.pk}/'
        self.assertEqual(client.get(url).status_code, 403)
        self.assertEqual(client.patch(url, {'owner_name': 'Changed'}, format='json').status_code, 403)
        self.vehicle.refresh_from_db()
        self.assertNotEqual(self.vehicle.owner_name, 'Changed')

    def test_sql_payload_cannot_broaden_vehicle_search(self):
        client = APIClient()
        client.force_authenticate(self.operator)
        response = client.get('/api/v1/vehicles/search/', {'plate': "' OR 1=1 --"})
        self.assertIn(response.status_code, (400, 404))
        self.assertEqual(Vehicle.objects.count(), 1)

    @override_settings(
        SECURE_SSL_REDIRECT=True, SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True,
        SESSION_SAVE_EVERY_REQUEST=True,
    )
    def test_production_redirect_and_secure_session_cookie(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers['Location'], 'https://testserver/api/auth/me/')
        self.client.force_login(self.operator)
        response = self.client.get('/admin/login/', secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.cookies[settings.CSRF_COOKIE_NAME]['secure'])
        self.assertTrue(response.cookies[settings.SESSION_COOKIE_NAME]['secure'])
