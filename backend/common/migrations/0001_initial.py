from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='AuditEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('occurred_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('actor_id', models.CharField(blank=True, editable=False, max_length=64, null=True)),
                ('actor_username', models.CharField(blank=True, editable=False, max_length=150)),
                ('actor_role', models.CharField(blank=True, editable=False, max_length=20)),
                ('ip_address', models.GenericIPAddressField(blank=True, editable=False, null=True)),
                ('event_type', models.CharField(db_index=True, editable=False, max_length=100)),
                ('resource_type', models.CharField(blank=True, editable=False, max_length=100)),
                ('resource_id', models.CharField(blank=True, editable=False, max_length=100)),
                ('details', models.JSONField(blank=True, default=dict, editable=False)),
            ],
            options={
                'ordering': ('-occurred_at', '-pk'),
                'base_manager_name': 'objects',
                'indexes': [models.Index(fields=['event_type', 'occurred_at'], name='audit_event_type_time')],
            },
        ),
    ]
