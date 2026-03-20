# Migración: agrega FK tipo_programa a las 4 tablas de configuración nutricional.
# Usa SeparateDatabaseAndState para minutapatronmeta porque el constraint
# unique_together puede no existir en la BD actual (fue omitido en algunos entornos).

import django.db.models.deletion
from django.db import migrations, models


def drop_minuta_patron_unique_if_exists(apps, schema_editor):
    """Elimina el constraint unique de MinutaPatronMeta solo si existe."""
    db = schema_editor.connection
    # Buscar el nombre exacto del constraint
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'nutricion_minuta_patron_rangos'
              AND constraint_type = 'UNIQUE'
              AND constraint_schema = current_schema()
        """)
        rows = cursor.fetchall()
        for row in rows:
            constraint_name = row[0]
            cursor.execute(
                f'ALTER TABLE nutricion_minuta_patron_rangos DROP CONSTRAINT IF EXISTS "{constraint_name}"'
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0041_equivalencia_icbf_por_menu'),
        ('principal', '0010_poblar_tipos_programa_y_nivel_general'),
    ]

    operations = [
        # --- AdecuacionTotalPorcentaje ---
        migrations.AlterUniqueTogether(
            name='adecuaciontotalporcentaje',
            unique_together=set(),
        ),
        # --- TablaRequerimientosNutricionales ---
        migrations.AlterUniqueTogether(
            name='tablarequerimientosnutricionales',
            unique_together=set(),
        ),
        # --- RecomendacionDiariaGradoMod ---
        migrations.AlterUniqueTogether(
            name='recomendaciondiariagradomod',
            unique_together=set(),
        ),
        # --- MinutaPatronMeta: usar SQL directo para no fallar si el constraint no existe ---
        migrations.RunPython(drop_minuta_patron_unique_if_exists, noop),
        # Actualizar estado del ORM para que sepa que el constraint ya no existe
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterUniqueTogether(
                    name='minutapatronmeta',
                    unique_together=set(),
                ),
            ],
        ),

        # --- Agregar FK tipo_programa a las 4 tablas ---
        migrations.AddField(
            model_name='adecuaciontotalporcentaje',
            name='tipo_programa',
            field=models.ForeignKey(
                blank=True, db_column='tipo_programa', null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='principal.tipoprograma', verbose_name='Tipo de Programa',
            ),
        ),
        migrations.AddField(
            model_name='minutapatronmeta',
            name='tipo_programa',
            field=models.ForeignKey(
                blank=True, db_column='tipo_programa', null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='principal.tipoprograma', verbose_name='Tipo de Programa',
            ),
        ),
        migrations.AddField(
            model_name='recomendaciondiariagradomod',
            name='tipo_programa',
            field=models.ForeignKey(
                blank=True, db_column='tipo_programa', null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='principal.tipoprograma', verbose_name='Tipo de Programa',
            ),
        ),
        migrations.AddField(
            model_name='tablarequerimientosnutricionales',
            name='tipo_programa',
            field=models.ForeignKey(
                blank=True, db_column='tipo_programa', null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='principal.tipoprograma', verbose_name='Tipo de Programa',
            ),
        ),

        # --- Recrear unique_together con tipo_programa incluido ---
        migrations.AlterUniqueTogether(
            name='adecuaciontotalporcentaje',
            unique_together={('id_nivel_escolar_uapa', 'id_modalidad', 'tipo_programa')},
        ),
        migrations.AlterUniqueTogether(
            name='minutapatronmeta',
            unique_together={('id_modalidad', 'id_grado_escolar_uapa', 'id_componente', 'id_grupo_alimentos', 'tipo_programa')},
        ),
        migrations.AlterUniqueTogether(
            name='recomendaciondiariagradomod',
            unique_together={('nivel_escolar_uapa', 'id_modalidades', 'tipo_programa')},
        ),
        migrations.AlterUniqueTogether(
            name='tablarequerimientosnutricionales',
            unique_together={('id_nivel_escolar_uapa', 'id_modalidad', 'tipo_programa')},
        ),
    ]
