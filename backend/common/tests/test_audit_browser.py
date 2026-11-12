from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from common.models import AuditEvent


class AuditBrowserTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_user(username='browser-admin', role='Admin')
        cls.when = datetime(2026, 11, 12, 9, tzinfo=timezone.utc)
        cls.first = AuditEvent.objects.create(
            event_type='account.updated', actor_id='17', actor_username='FormerOperator',
            actor_role='Admin', resource_type='user', resource_id='23', occurred_at=cls.when,
            details={'previous_state': {'role': 'Operator'}, 'new_state': {'role': 'Customer'}},
        )
        cls.second = AuditEvent.objects.create(
            event_type='auth.login_failed', resource_type='user', occurred_at=cls.when,
            details={'outcome': 'failure'},
        )
        cls.third = AuditEvent.objects.create(
            event_type='parking_zone.deactivated', actor_id='42', actor_username='FormerOperator',
            actor_role='Operator', resource_type='parking_zone', occurred_at=cls.when.replace(hour=10),
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def ids(self, **params):
        response = self.client.get('/api/audit/', params)
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response['Cache-Control'])
        return [event['id'] for event in response.data['results']]

    def test_combined_action_actor_resource_and_date_filters(self):
        self.assertEqual(self.ids(event_type='account.updated', actor='formeroperator', resource_type='user',
                                  start='2026-11-12T14:30:00+05:30', end='2026-11-12T15:30:00+05:30'), [self.first.pk])

    def test_actor_snapshot_search_and_existing_exact_id_filter(self):
        self.assertEqual(self.ids(actor='Former'), [self.third.pk, self.first.pk])
        self.assertEqual(self.ids(actor='17'), [self.first.pk])
        self.assertEqual(self.ids(actor_id='17'), [self.first.pk])
        self.assertEqual(self.ids(actor='missing'), [])
        self.assertEqual(self.ids(resource_type='parking_zone'), [self.third.pk])

    def test_date_boundaries_and_open_ended_ranges(self):
        self.assertEqual(self.ids(start='2026-11-12T09:00:00Z', end='2026-11-12T10:00:00Z'), [self.second.pk, self.first.pk])
        self.assertEqual(self.ids(start='2026-11-12T10:00:00Z'), [self.third.pk])
        self.assertEqual(self.ids(end='2026-11-12T09:00:00Z'), [])

    def test_invalid_filters_return_shared_validation_error(self):
        for params in ({'start': 'invalid'}, {'end': 'not-a-date'},
                       {'start': '2026-11-12T10:00:00Z', 'end': '2026-11-12T09:00:00Z'},
                       {'start': '2026-11-12T09:00:00Z', 'end': '2026-11-12T09:00:00Z'},
                       {'actor': 'a' * 151}, {'actor_id': '1' * 65}, {'resource_type': 'x' * 101}):
            with self.subTest(params=params):
                response = self.client.get('/api/audit/', params)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(set(response.data), {'error', 'code', 'details'})
                self.assertEqual(response.data['code'], 'VALIDATION_ERROR')
                self.assertIn('no-store', response['Cache-Control'])

    def test_pagination_preserves_filters_and_state_snapshots(self):
        first = self.client.get('/api/audit/', {'actor': 'Former', 'page_size': 1})
        self.assertEqual(first.data['count'], 2)
        self.assertIn('actor=Former', first.data['next'])
        self.assertEqual(first.data['results'][0]['id'], self.third.pk)
        second = self.client.get(first.data['next'])
        self.assertEqual(second.data['results'][0]['id'], self.first.pk)
        self.assertEqual(second.data['results'][0]['details'], self.first.details)

    def test_permissions_precede_filter_validation_and_writes_stay_forbidden(self):
        for role in ('Operator', 'Customer'):
            user = get_user_model().objects.create_user(username=role, role=role)
            self.client.force_authenticate(user)
            response = self.client.get('/api/audit/', {'start': 'invalid', 'role': 'Admin'})
            self.assertEqual(response.status_code, 403)
        self.client.force_authenticate(self.admin)
        for method in ('post', 'put', 'patch', 'delete'):
            response = getattr(self.client, method)('/api/audit/', {'event_type': 'tampered'}, format='json')
            self.assertEqual(response.status_code, 405)
        self.assertEqual(AuditEvent.objects.count(), 3)
        self.first.refresh_from_db()
        self.assertEqual(self.first.event_type, 'account.updated')
