"""
Migración 0044:
- Hace nullable calcio/hierro/sodio en TablaRequerimientosNutricionales
  y AdecuacionTotalPorcentaje (Comedores Comunitarios y Adulto Mayor no los evalúan).
- Inserta registros de requerimientos nutricionales para comedores_comunitarios
  y adulto_mayor con nivel 'general' y modalidad '020701'.
"""
from django.db import migrations, models


def insertar_requerimientos_comedores(apps, schema_editor):
    TablaRequerimientosNutricionales = apps.get_model('nutricion', 'TablaRequerimientosNutricionales')
    AdecuacionTotalPorcentaje = apps.get_model('nutricion', 'AdecuacionTotalPorcentaje')
    ModalidadesDeConsumo = apps.get_model('principal', 'ModalidadesDeConsumo')

    # Garantizar que la modalidad '020701' exista (es dato maestro que puede no estar en BD de prueba)
    ModalidadesDeConsumo.objects.get_or_create(
        id_modalidades='020701',
        defaults={'modalidad': 'RACIONES PARA PREPARAR'},
    )

    for tipo_id in ['comedores_comunitarios', 'adulto_mayor']:
        TablaRequerimientosNutricionales.objects.get_or_create(
            id_requerimiento_nutricional=f'req_general_{tipo_id}',
            defaults={
                'calorias_kcal': 1830.0,
                'proteina_g': 59.5,
                'grasa_g': 54.9,
                'cho_g': 275.0,
                'calcio_mg': None,
                'hierro_mg': None,
                'sodio_mg': None,
                'id_nivel_escolar_uapa_id': 'general',
                'id_modalidad_id': '020701',
                'tipo_programa_id': tipo_id,
            },
        )
        AdecuacionTotalPorcentaje.objects.get_or_create(
            id_adecuacion_porcentaje=f'adec_general_{tipo_id}',
            defaults={
                'calorias_porc': 40.0,
                'proteina_porc': 40.0,
                'grasa_porc': 40.0,
                'cho_porc': 40.0,
                'calcio_porc': None,
                'hierro_porc': None,
                'sodio_porc': None,
                'id_nivel_escolar_uapa_id': 'general',
                'id_modalidad_id': '020701',
                'tipo_programa_id': tipo_id,
            },
        )


def revertir(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0043_poblar_tipo_programa_pae_config_tables'),
        ('principal', '0010_poblar_tipos_programa_y_nivel_general'),
    ]

    operations = [
        # Hacer nullable calcio/hierro/sodio en requerimientos
        migrations.AlterField(
            model_name='tablarequerimientosnutricionales',
            name='calcio_mg',
            field=models.DecimalField(
                decimal_places=1, max_digits=10,
                null=True, blank=True, verbose_name='Calcio (mg)'
            ),
        ),
        migrations.AlterField(
            model_name='tablarequerimientosnutricionales',
            name='hierro_mg',
            field=models.DecimalField(
                decimal_places=1, max_digits=10,
                null=True, blank=True, verbose_name='Hierro (mg)'
            ),
        ),
        migrations.AlterField(
            model_name='tablarequerimientosnutricionales',
            name='sodio_mg',
            field=models.DecimalField(
                decimal_places=1, max_digits=10,
                null=True, blank=True, verbose_name='Sodio (mg)'
            ),
        ),
        # Hacer nullable calcio/hierro/sodio en adecuación porcentaje
        migrations.AlterField(
            model_name='adecuaciontotalporcentaje',
            name='calcio_porc',
            field=models.DecimalField(
                decimal_places=1, max_digits=5,
                null=True, blank=True, verbose_name='Calcio (%)'
            ),
        ),
        migrations.AlterField(
            model_name='adecuaciontotalporcentaje',
            name='hierro_porc',
            field=models.DecimalField(
                decimal_places=1, max_digits=5,
                null=True, blank=True, verbose_name='Hierro (%)'
            ),
        ),
        migrations.AlterField(
            model_name='adecuaciontotalporcentaje',
            name='sodio_porc',
            field=models.DecimalField(
                decimal_places=1, max_digits=5,
                null=True, blank=True, verbose_name='Sodio (%)'
            ),
        ),
        # Insertar datos para Comedores Comunitarios y Adulto Mayor
        migrations.RunPython(insertar_requerimientos_comedores, revertir),
    ]
