from django.db import migrations, models
from django.db.models import Q
from django.db.models.functions import Lower


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(Lower("username"), name="accounts_username_ci_unique"),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(Lower("email"), condition=~Q(email=""), name="accounts_email_ci_unique"),
        ),
    ]
