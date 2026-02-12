# Generated manually 2026-02-12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0009_renombrar_tabla_ingredientes_por_nivel'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='tablaanalisisnutricionalmenu',
            table='nutricion_tabla_analisis_nutricional_menu',
        ),
    ]
