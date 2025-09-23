from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('MyApi', '0006_alter_elocalculation_options_and_more'),
    ]

    # This migration used to rename `elo_rating` -> `elo`.
    # The codebase and database already use `elo` so attempting to rename
    # will raise FieldDoesNotExist. Keep a no-op migration to satisfy
    # Django's migration history.
    operations = [
        migrations.RunPython(lambda apps, schema_editor: None, reverse_code=lambda apps, schema_editor: None),
    ]
