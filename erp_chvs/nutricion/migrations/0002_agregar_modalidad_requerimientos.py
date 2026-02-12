# Generated manually - Febrero 2025
# Agrega campo id_modalidad a TablaRequerimientosNutricionales
# y actualiza unique_together para incluir nivel + modalidad

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('principal', '0001_initial'),  # Asegura que ModalidadesDeConsumo existe
        ('nutricion', '0001_initial'),
    ]

    operations = [
        # Paso 1: Eliminar la restricción unique_together antigua
        migrations.AlterUniqueTogether(
            name='tablarequerimientosnutricionales',
            unique_together=set(),
        ),

        # Paso 2: Agregar el campo id_modalidad (permitir NULL inicialmente)
        migrations.AddField(
            model_name='tablarequerimientosnutricionales',
            name='id_modalidad',
            field=models.ForeignKey(
                blank=True,
                db_column='id_modalidad',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='requerimientos_nutricionales',
                to='principal.modalidadesdeconsumo',
                verbose_name='Modalidad de Consumo'
            ),
        ),

        # Paso 3: Actualizar unique_together para nivel + modalidad
        migrations.AlterUniqueTogether(
            name='tablarequerimientosnutricionales',
            unique_together={('id_nivel_escolar_uapa', 'id_modalidad')},
        ),

        # Paso 4: Actualizar ordering
        migrations.AlterModelOptions(
            name='tablarequerimientosnutricionales',
            options={
                'ordering': ['id_nivel_escolar_uapa', 'id_modalidad'],
                'verbose_name': 'Requerimiento Nutricional',
                'verbose_name_plural': 'Requerimientos Nutricionales'
            },
        ),
    ]
