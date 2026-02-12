# Generated manually 2026-02-12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0002_agregar_modalidad_requerimientos'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='componentesalimentos',
            table='nutricion_componentes_alimentos',
        ),
    ]
