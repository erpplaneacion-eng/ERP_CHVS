# Generated manually 2026-02-12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0007_renombrar_tabla_preparaciones'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='tablapreparacioningredientes',
            table='nutricion_tabla_preparacion_ingredientes',
        ),
    ]
