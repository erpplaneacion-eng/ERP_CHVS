# Generated manually on 2026-02-16
# Corrección de db_table (minúsculas) y db_column para ForeignKey programa

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0002_rename_listados_fo_ano_e04e90_idx_facturacion_ano_527684_idx_and_more'),
        ('planeacion', '0001_initial'),
    ]

    operations = [
        # Corregir nombre de tabla a minúsculas (PostgreSQL case-sensitive)
        # Si la tabla ya está en minúsculas, esta operación no hace nada
        migrations.AlterModelTable(
            name='listadosfocalizacion',
            table='facturacion_listados_focalizacion',
        ),
        # Agregar db_column explícito al ForeignKey programa
        # Si la columna ya es programa_id, no hace cambios en DB
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
