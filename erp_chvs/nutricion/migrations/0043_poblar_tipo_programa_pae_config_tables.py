from django.db import migrations


def poblar_tipo_programa_pae(apps, schema_editor):
    TablaRequerimientosNutricionales = apps.get_model('nutricion', 'TablaRequerimientosNutricionales')
    AdecuacionTotalPorcentaje = apps.get_model('nutricion', 'AdecuacionTotalPorcentaje')
    RecomendacionDiariaGradoMod = apps.get_model('nutricion', 'RecomendacionDiariaGradoMod')

    TablaRequerimientosNutricionales.objects.filter(tipo_programa__isnull=True).update(tipo_programa_id='pae')
    AdecuacionTotalPorcentaje.objects.filter(tipo_programa__isnull=True).update(tipo_programa_id='pae')
    RecomendacionDiariaGradoMod.objects.filter(tipo_programa__isnull=True).update(tipo_programa_id='pae')


def poblar_minuta_patron_pae(apps, schema_editor):
    """
    MinutaPatronMeta puede tener filas duplicadas por la misma combinación
    (id_modalidad, id_grado_escolar_uapa, id_componente, id_grupo_alimentos)
    ya que el constraint unique no se aplicaba en la BD.

    Estrategia: para cada grupo duplicado, mantener solo la primera fila (por id)
    y eliminar las demás, luego actualizar tipo_programa='pae'.
    """
    from django.db import connection

    with connection.cursor() as cursor:
        # Eliminar duplicados: mantener el de id menor por cada combinación (4 campos)
        cursor.execute("""
            DELETE FROM nutricion_minuta_patron_rangos
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM nutricion_minuta_patron_rangos
                WHERE tipo_programa IS NULL
                GROUP BY id_modalidad, id_grado_escolar_uapa, id_componente, id_grupo_alimentos
            )
            AND tipo_programa IS NULL
        """)
        # Actualizar los registros restantes (únicos) con tipo_programa='pae'
        cursor.execute("""
            UPDATE nutricion_minuta_patron_rangos
            SET tipo_programa = 'pae'
            WHERE tipo_programa IS NULL
        """)


def revertir(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    # No-atómica para manejar los duplicados en MinutaPatronMeta sin revertir todo
    atomic = False

    dependencies = [
        ('nutricion', '0042_add_tipo_programa_to_config_tables'),
        ('principal', '0010_poblar_tipos_programa_y_nivel_general'),
    ]

    operations = [
        migrations.RunPython(poblar_tipo_programa_pae, revertir),
        migrations.RunPython(poblar_minuta_patron_pae, revertir),
    ]
