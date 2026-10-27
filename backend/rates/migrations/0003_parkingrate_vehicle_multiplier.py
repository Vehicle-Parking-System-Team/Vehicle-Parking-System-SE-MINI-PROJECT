from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('rates', '0002_alter_parkingrate_grace_period_minutes'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkingrate',
            name='vehicle_multiplier',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('1.00'),
                max_digits=5,
                validators=[MinValueValidator(0)],
            ),
        ),
    ]
