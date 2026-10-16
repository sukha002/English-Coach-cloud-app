# Generated initial migration for the MVP.
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Transcript",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("owner_key", models.CharField(db_index=True, max_length=80)),
                ("original_text", models.TextField()),
                ("corrected_text", models.TextField()),
                ("corrections", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
