from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('parking_slots', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='parkingslot',
            name='floor',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
