# Generated manually 2026-02-12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0005_renombrar_tabla_grupos_alimentos'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='tablamenus',
            table='nutricion_tabla_menus',
        ),
    ]
