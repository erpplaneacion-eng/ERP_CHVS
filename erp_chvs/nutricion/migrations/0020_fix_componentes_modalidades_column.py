# Generated manually to align db_column with legacy schema in production DBs.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0019_rename_nutricion_r_modalid_4d33e5_idx_nutricion_r_modalid_e1a6d0_idx_and_more'),
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
                            FROM information_schema.columns
                            WHERE table_name = 'nutricion_componentes_modalidades'
                              AND column_name = 'id_modalidad'
                        )
                        AND NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'nutricion_componentes_modalidades'
                              AND column_name = 'id_modalidades'
                        ) THEN
                            ALTER TABLE nutricion_componentes_modalidades
                            RENAME COLUMN id_modalidad TO id_modalidades;
                        END IF;
                    END $$;
                    """,
                    reverse_sql="""
                    DO $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'nutricion_componentes_modalidades'
                              AND column_name = 'id_modalidades'
                        )
                        AND NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'nutricion_componentes_modalidades'
                              AND column_name = 'id_modalidad'
                        ) THEN
                            ALTER TABLE nutricion_componentes_modalidades
                            RENAME COLUMN id_modalidades TO id_modalidad;
                        END IF;
                    END $$;
                    """,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='componentesmodalidades',
                    name='id_modalidad',
                    field=models.ForeignKey(
                        db_column='id_modalidades',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='componentes_modalidades',
                        to='principal.modalidadesdeconsumo',
                        verbose_name='Modalidad de Consumo',
                    ),
                ),
            ],
        ),
    ]
