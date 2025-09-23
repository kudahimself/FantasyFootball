from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('MyApi', '0007_rename_elocalculation_field'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "DROP INDEX IF EXISTS elo_calcula_elo_rat_5b3371_idx;",
                "CREATE INDEX IF NOT EXISTS idx_elo_calculations_elo ON elo_calculations(elo DESC);"
            ],
            reverse_sql=[
                # Optionally recreate the old index if you ever reverse this migration
            ]
        ),
    ]
