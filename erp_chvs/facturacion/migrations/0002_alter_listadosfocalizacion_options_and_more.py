# Generated manually on 2026-02-16
# Corrección de db_table y db_column para coincid con la base de datos existente

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0001_initial'),
        ('planeacion', '0001_initial'),
    ]

    operations = [
        # Actualizar db_table a minúsculas (sin cambios reales en DB si ya está correcta)
        migrations.AlterModelTable(
            name='listadosfocalizacion',
            table='facturacion_listados_focalizacion',
        ),
        # Agregar db_column explícito al ForeignKey programa
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
