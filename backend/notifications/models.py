from django.conf import settings
from django.db import models


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    kind = models.CharField(max_length=32)
    event_key = models.CharField(max_length=100)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-pk']
        constraints = [models.UniqueConstraint(fields=['recipient', 'event_key'], name='notification_recipient_event')]
        indexes = [models.Index(fields=['recipient', 'read_at', '-id'], name='notification_unread')]
