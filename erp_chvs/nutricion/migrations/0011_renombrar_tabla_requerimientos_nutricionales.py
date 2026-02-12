# Generated manually 2026-02-12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0010_renombrar_tabla_analisis_nutricional_menu'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='tablarequerimientosnutricionales',
            table='nutricion_total_aporte_promedio_diario',
        ),
    ]
