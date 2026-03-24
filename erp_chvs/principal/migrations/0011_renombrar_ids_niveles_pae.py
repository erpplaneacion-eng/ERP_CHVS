from django.db import migrations

# Mapeo de IDs numéricos (en DB) → IDs descriptivos (esperados por el código)
MAPPING = {
    '100': 'prescolar',
    '123': 'primaria_1_2_3',
    '45': 'primaria_4_5',
    '6789': 'secundaria',
    '1011': 'media_ciclo_complementario',
}


def renombrar_ids_niveles(apps, schema_editor):
    """
    Renombra los PKs numéricos de TablaGradosEscolaresUapa a los IDs descriptivos
    que el código espera ('prescolar', 'primaria_1_2_3', etc.).

    Estrategia 3 pasos para evitar violaciones de FK:
      1. Insertar nuevos registros padre con IDs descriptivos
      2. Actualizar todas las tablas hijas apuntando a los nuevos IDs
      3. Eliminar los registros padre con IDs numéricos
    """
    db = schema_editor.connection
    with db.cursor() as cursor:
        # ── Paso 1: insertar nuevos registros padre ──────────────────────────
        for old_id, new_id in MAPPING.items():
            cursor.execute(
                "INSERT INTO tabla_grados_escolares_uapa (id_grado_escolar_uapa, nivel_escolar_uapa) "
                "SELECT %s, nivel_escolar_uapa FROM tabla_grados_escolares_uapa "
                "WHERE id_grado_escolar_uapa = %s",
                [new_id, old_id],
            )

        # ── Paso 2: actualizar todas las tablas hijas ─────────────────────────
        TABLAS_HIJAS = [
            # (nombre_tabla, columna_fk)
            ('nivel_grado_escolar',                          'nivel_escolar_uapa'),
            ('nutricion_tabla_analisis_nutricional_menu',    'id_nivel_escolar_uapa'),
            ('nutricion_total_aporte_promedio_diario',       'id_nivel_escolar_uapa'),
            ('nutricion_adecuacion_total_porc',              'id_nivel_escolar_uapa'),
            ('nutricion_minuta_patron_rangos',               'id_grado_escolar_uapa'),
            ('nutricion_recomendacion_diaria_por_grado_mod', 'nivel_escolar_uapa'),
        ]
        for old_id, new_id in MAPPING.items():
            for tabla, columna in TABLAS_HIJAS:
                cursor.execute(
                    f"UPDATE {tabla} SET {columna} = %s WHERE {columna} = %s",
                    [new_id, old_id],
                )

        # ── Paso 3: eliminar los registros padre con IDs numéricos ────────────
        for old_id in MAPPING.keys():
            cursor.execute(
                "DELETE FROM tabla_grados_escolares_uapa WHERE id_grado_escolar_uapa = %s",
                [old_id],
            )


def revertir(apps, schema_editor):
    pass  # No se implementa reversión automática


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0010_poblar_tipos_programa_y_nivel_general'),
        # Las tablas nutricion_* se crean/renombran antes de esta migración de datos
        ('nutricion', '0027_recomendacion_diaria_grado_mod'),
    ]

    operations = [
        migrations.RunPython(renombrar_ids_niveles, revertir),
    ]
