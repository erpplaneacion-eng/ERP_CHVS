# Generated manually 2026-02-12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0008_renombrar_tabla_preparacion_ingredientes'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='tablaingredientespornivel',
            table='nutricion_tabla_ingredientes_por_nivel',
        ),
    ]
