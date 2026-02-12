# Generated manually 2026-02-12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0006_renombrar_tabla_menus'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='tablapreparaciones',
            table='nutricion_tabla_preparaciones',
        ),
    ]
