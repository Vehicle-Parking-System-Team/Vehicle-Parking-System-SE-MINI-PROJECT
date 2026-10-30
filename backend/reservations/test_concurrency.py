"""PostgreSQL regression: concurrent overlapping bookings must serialize per slot."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connections
from django.test import TransactionTestCase, skipUnlessDBFeature
from django.utils import timezone
from rest_framework.test import APIClient

from parking_slots.models import ParkingSlot, ParkingZone
from vehicles.models import Vehicle
from .models import Reservation


class PostgreSQLReservationConcurrencyTests(TransactionTestCase):
    databases = {'default'}

    def test_two_overlapping_requests_yield_one_201_and_one_409(self):
        if connections['default'].vendor != 'postgresql':
            self.skipTest('Requires PostgreSQL row-level locks')

        user = get_user_model().objects.create_user(
            username='concurrent_customer_13', role='Customer',
        )
        vehicle = Vehicle.objects.create(
            registration_number='KA01CC1313', vehicle_type='Compact', owner=user,
        )
        zone = ParkingZone.objects.create(name='Concurrent Reservations')
        slot = ParkingSlot.objects.create(
            zone=zone, slot_number='C-13', floor=0, vehicle_type='Compact',
        )
        payload = {
            'vehicle': vehicle.pk,
            'slot': slot.pk,
            'start_time': (timezone.now() + timedelta(days=2)).isoformat(),
            'duration_minutes': 60,
        }
        barrier = Barrier(2, timeout=15)

        def reserve():
            close_old_connections()
            try:
                client = APIClient()
                client.force_authenticate(user=user)
                barrier.wait()
                response = client.post(
                    '/api/parking/reservations/', payload, format='json',
                )
                return response.status_code
            finally:
                connections['default'].close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(reserve)
            second = pool.submit(reserve)
            statuses = sorted([first.result(timeout=30), second.result(timeout=30)])

        self.assertEqual(statuses, [201, 409])
        self.assertEqual(
            Reservation.objects.filter(
                slot=slot, status=Reservation.Status.CONFIRMED,
            ).count(), 1,
        )
