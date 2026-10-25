
from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "operations",
            "0002_parkingrecord_delete_parkingsession_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="parkingrecord",
            name="fee_amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                validators=[MinValueValidator(0)],
            ),
        ),
    ]
