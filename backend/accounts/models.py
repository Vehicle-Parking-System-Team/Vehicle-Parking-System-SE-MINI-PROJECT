from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


class AccountUserManager(UserManager):
    """Keep Django's createsuperuser command aligned with domain RBAC."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'Admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model aligning with SAD Section 4.1 data model."""

    ROLE_CHOICES = [
        ('Admin', 'Administrator'),
        ('Operator', 'Operator'),
        ('Customer', 'Customer'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('deactivated', 'Deactivated'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='Customer',
        help_text='User authorization role (Admin, Operator, Customer).',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text='Account lifecycle status (active, suspended, deactivated).',
    )
    token_version = models.PositiveIntegerField(
        default=1,
        help_text='Token generation version incremented upon logout for immediate access token revocation.',
    )

    phone_number = models.CharField(max_length=20, blank=True, default='', db_default='', help_text='User contact phone number.')

    objects = AccountUserManager()

    class Meta:
        db_table = 'users'
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(Lower('username'), name='accounts_username_ci_unique'),
            models.UniqueConstraint(Lower('email'), condition=~Q(email=''), name='accounts_email_ci_unique'),
        ]

    def __str__(self):
        return f'{self.username} ({self.role})'

    @property
    def is_account_active(self):
        """Check both Django native is_active flag and domain status."""
        return self.is_active and self.status == 'active'
