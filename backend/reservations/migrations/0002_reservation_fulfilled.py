from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('reservations', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='status',
            field=models.CharField(
                choices=[
                    ('Confirmed', 'Confirmed'),
                    ('Cancelled', 'Cancelled'),
                    ('Fulfilled', 'Fulfilled'),
                ],
                default='Confirmed',
                max_length=12,
            ),
        ),
    ]
