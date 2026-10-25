"""
Idempotent management command to seed safe development and evaluation users.
US-01 / DEC-13 / SAD §3.4.2 & §5.1.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from accounts.models import User


class Command(BaseCommand):
    help = 'Seeds safe local development and evaluation test users for US-01.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            help='Reset passwords for existing demo users to default test password.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force execution even if DEBUG is False.',
        )

    def handle(self, *args, **options):
        import sys
        is_testing = 'test' in sys.argv
        if not settings.DEBUG and not options.get('force') and not is_testing:
            raise CommandError(
                'seed_demo_users is restricted to local development environments (DEBUG=True). '
                'Pass --force to override.'
            )

        users_data = [
            {
                'username': 'operator1',
                'email': 'operator1@parking.local',
                'role': 'Operator',
                'status': 'active',
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'admin',
                'email': 'admin@parking.local',
                'role': 'Admin',
                'status': 'active',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'customer1',
                'email': 'customer1@parking.local',
                'role': 'Customer',
                'status': 'active',
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'suspended_user',
                'email': 'suspended@parking.local',
                'role': 'Customer',
                'status': 'suspended',
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'inactive_user',
                'email': 'inactive@parking.local',
                'role': 'Customer',
                'status': 'active',
                'is_active': False,
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        default_password = 'SecurePass123!'
        should_reset_existing_passwords = options.get('reset_passwords', False)

        created_count = 0
        updated_count = 0

        for user_info in users_data:
            username = user_info['username']
            user = User.objects.filter(username=username).first()
            is_new = user is None

            if is_new:
                user = User(username=username)
                created_count += 1
            else:
                updated_count += 1

            user.email = user_info['email']
            user.role = user_info['role']
            user.status = user_info['status']
            user.is_active = user_info['is_active']
            user.is_staff = user_info['is_staff']
            user.is_superuser = user_info['is_superuser']

            # Only set password on initial creation or when explicitly requested
            if is_new or should_reset_existing_passwords:
                user.set_password(default_password)

            user.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Configured user "{username}" (Role: {user.role}, Status: {user.status}, Active: {user.is_active})'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed complete. {created_count} users created, {updated_count} users updated.'
            )
        )
