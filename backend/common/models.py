"""Append-only audit events for security and operational actions."""

from django.db import models
from django.utils import timezone


class ImmutableAuditQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise TypeError('Audit events are immutable.')

    def delete(self):
        raise TypeError('Audit events cannot be deleted.')

    def bulk_update(self, objs, fields, **kwargs):
        raise TypeError('Audit events are immutable.')

    def bulk_create(self, objs, **kwargs):
        if kwargs.get('update_conflicts'):
            raise TypeError('Audit events are immutable.')
        return super().bulk_create(objs, **kwargs)


class AuditEvent(models.Model):
    """An append-only snapshot; actor/resource strings survive source deletion."""

    occurred_at = models.DateTimeField(default=timezone.now, db_index=True, editable=False)
    actor_id = models.CharField(max_length=64, null=True, blank=True, editable=False)
    actor_username = models.CharField(max_length=150, blank=True, editable=False)
    actor_role = models.CharField(max_length=20, blank=True, editable=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True, editable=False)
    event_type = models.CharField(max_length=100, db_index=True, editable=False)
    resource_type = models.CharField(max_length=100, blank=True, editable=False)
    resource_id = models.CharField(max_length=100, blank=True, editable=False)
    details = models.JSONField(default=dict, blank=True, editable=False)

    objects = ImmutableAuditQuerySet.as_manager()

    class Meta:
        ordering = ('-occurred_at', '-pk')
        base_manager_name = 'objects'
        indexes = [
            models.Index(fields=('event_type', 'occurred_at'), name='audit_event_type_time'),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding or self.pk is not None:
            raise TypeError('Audit events are immutable.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise TypeError('Audit events cannot be deleted.')

    def __str__(self):
        return f'{self.event_type} at {self.occurred_at.isoformat()}'
