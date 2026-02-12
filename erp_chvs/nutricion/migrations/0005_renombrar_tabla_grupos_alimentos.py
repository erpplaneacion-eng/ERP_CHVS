# Generated manually 2026-02-12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0004_requerimiento_semanal'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='gruposalimentos',
            table='nutricion_grupos_alimento',
        ),
    ]
