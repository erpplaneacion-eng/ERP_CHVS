# Generated manually to keep migration state aligned after column fix.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0020_fix_componentes_modalidades_column'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1
                            FROM pg_indexes
                            WHERE schemaname = current_schema()
                              AND indexname = 'nutricion_c_id_moda_c83791_idx'
                        )
                        AND NOT EXISTS (
                            SELECT 1
                            FROM pg_indexes
                            WHERE schemaname = current_schema()
                              AND indexname = 'nutricion_c_id_moda_8d8f38_idx'
                        ) THEN
                            ALTER INDEX nutricion_c_id_moda_c83791_idx
                            RENAME TO nutricion_c_id_moda_8d8f38_idx;
                        END IF;
                    END $$;
                    """,
                    reverse_sql="""
                    DO $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1
                            FROM pg_indexes
                            WHERE schemaname = current_schema()
                              AND indexname = 'nutricion_c_id_moda_8d8f38_idx'
                        )
                        AND NOT EXISTS (
                            SELECT 1
                            FROM pg_indexes
                            WHERE schemaname = current_schema()
                              AND indexname = 'nutricion_c_id_moda_c83791_idx'
                        ) THEN
                            ALTER INDEX nutricion_c_id_moda_8d8f38_idx
                            RENAME TO nutricion_c_id_moda_c83791_idx;
                        END IF;
                    END $$;
                    """,
                ),
            ],
            state_operations=[
                migrations.RenameIndex(
                    model_name='componentesmodalidades',
                    old_name='nutricion_c_id_moda_c83791_idx',
                    new_name='nutricion_c_id_moda_8d8f38_idx',
                ),
            ],
        ),
    ]
