from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0004_recallnote"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
