# Generated manually on 2026-02-16
# Corrección de db_table (minúsculas) y db_column para ForeignKey programa
# Migración idempotente: solo hace cambios si es necesario

import django.db.models.deletion
from django.db import migrations, models


def table_exists(schema_editor, table_name):
    """Verifica si una tabla existe en la base de datos"""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            );
        """, [table_name])
        return cursor.fetchone()[0]


def rename_table_if_needed(apps, schema_editor):
    """
    Renombra la tabla de facturacion_Listados_Focalizacion a
    facturacion_listados_focalizacion solo si la tabla antigua existe.
    """
    old_table = 'facturacion_Listados_Focalizacion'
    new_table = 'facturacion_listados_focalizacion'

    # Verificar si la tabla antigua existe
    if table_exists(schema_editor, old_table):
        # Renombrar tabla
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(f'ALTER TABLE "{old_table}" RENAME TO "{new_table}"')
    # Si la tabla nueva ya existe, no hacer nada
    elif table_exists(schema_editor, new_table):
        pass  # La tabla ya está correctamente nombrada
    else:
        # Ninguna de las dos existe, algo anda mal
        raise Exception(
            f"No se encontró ninguna tabla de listados de focalización. "
            f"Buscadas: {old_table}, {new_table}"
        )


def reverse_rename_table(apps, schema_editor):
    """Revertir el renombrado de tabla"""
    old_table = 'facturacion_Listados_Focalizacion'
    new_table = 'facturacion_listados_focalizacion'

    if table_exists(schema_editor, new_table):
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(f'ALTER TABLE "{new_table}" RENAME TO "{old_table}"')


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0002_rename_listados_fo_ano_e04e90_idx_facturacion_ano_527684_idx_and_more'),
        ('planeacion', '0001_initial'),
    ]

    operations = [
        # Renombrar tabla solo si es necesario (idempotente)
        migrations.RunPython(
            rename_table_if_needed,
            reverse_rename_table,
        ),
        # Agregar db_column explícito al ForeignKey programa
        # Django detecta automáticamente si la columna ya es programa_id
        migrations.AlterField(
            model_name='listadosfocalizacion',
            name='programa',
            field=models.ForeignKey(
                blank=True,
                db_column='programa_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='planeacion.programa',
                verbose_name='Programa'
            ),
        ),
    ]
