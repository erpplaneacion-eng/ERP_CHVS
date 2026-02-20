from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Cambia RequerimientoSemanal para agrupar por GruposAlimentos
    en lugar de ComponentesAlimentos.

    - Elimina datos existentes (incompatibles con el nuevo esquema)
    - Quita campo 'componente' (FK → ComponentesAlimentos)
    - Agrega campo 'grupo' (FK → GruposAlimentos)
    - Actualiza unique_together, índices y ordering

    Nota: el unique_together (modalidad, componente) no existía físicamente
    en la BD (solo en el estado de migraciones), por lo que se usa
    SeparateDatabaseAndState para actualizar solo el estado de Django.
    """

    dependencies = [
        ('nutricion', '0023_alimentos_icbf_campos_decimales'),
    ]

    operations = [
        # 1. Limpiar datos existentes (incompatibles con el nuevo FK)
        migrations.RunSQL(
            sql="DELETE FROM nutricion_requerimientos_semanales;",
            reverse_sql=migrations.RunSQL.noop,
        ),

        # 2. Quitar unique_together que incluye 'componente'
        #    La restricción no existe físicamente en la BD, solo en el estado
        #    de migraciones → usamos SeparateDatabaseAndState para actualizar
        #    solo el estado sin ejecutar nada en la BD.
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterUniqueTogether(
                    name='requerimientosemanal',
                    unique_together=set(),
                ),
            ],
        ),

        # 3. Quitar índice sobre 'componente' de forma tolerante.
        #    En algunos entornos el nombre puede variar por migraciones previas.
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        DROP INDEX IF EXISTS nutricion_r_compone_94b87e_idx;
                        DROP INDEX IF EXISTS nutricion_r_compone_f7553a_idx;
                        DROP INDEX IF EXISTS nutricion_r_compone_idx;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.RemoveIndex(
                    model_name='requerimientosemanal',
                    name='nutricion_r_compone_94b87e_idx',
                ),
            ],
        ),

        # 4. Quitar campo 'componente' de forma tolerante.
        #    Debido a desalineación histórica entre estado y BD, la columna física
        #    puede llamarse 'componente_id' o 'componente'.
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        DO $$
                        BEGIN
                            IF EXISTS (
                                SELECT 1
                                FROM information_schema.columns
                                WHERE table_schema = 'public'
                                  AND table_name = 'nutricion_requerimientos_semanales'
                                  AND column_name = 'modalidad'
                            )
                            AND NOT EXISTS (
                                SELECT 1
                                FROM information_schema.columns
                                WHERE table_schema = 'public'
                                  AND table_name = 'nutricion_requerimientos_semanales'
                                  AND column_name = 'modalidad_id'
                            ) THEN
                                ALTER TABLE nutricion_requerimientos_semanales
                                RENAME COLUMN modalidad TO modalidad_id;
                            END IF;
                        END $$;

                        ALTER TABLE nutricion_requerimientos_semanales
                        DROP COLUMN IF EXISTS componente_id CASCADE;
                        ALTER TABLE nutricion_requerimientos_semanales
                        DROP COLUMN IF EXISTS componente CASCADE;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name='requerimientosemanal',
                    name='componente',
                ),
            ],
        ),

        # 5. Agregar campo 'grupo'
        migrations.AddField(
            model_name='requerimientosemanal',
            name='grupo',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='requerimientos_semanales',
                to='nutricion.gruposalimentos',
                verbose_name='Grupo de Alimentos',
            ),
            preserve_default=False,
        ),

        # 6. Agregar índice sobre 'grupo'
        migrations.AddIndex(
            model_name='requerimientosemanal',
            index=models.Index(fields=['grupo'], name='nutricion_r_grupo_idx'),
        ),

        # 7. Restaurar unique_together con 'grupo'
        migrations.AlterUniqueTogether(
            name='requerimientosemanal',
            unique_together={('modalidad', 'grupo')},
        ),

        # 8. Actualizar ordering
        migrations.AlterModelOptions(
            name='requerimientosemanal',
            options={
                'ordering': ['modalidad', 'grupo'],
                'verbose_name': 'Requerimiento Semanal',
                'verbose_name_plural': 'Requerimientos Semanales',
            },
        ),
    ]
