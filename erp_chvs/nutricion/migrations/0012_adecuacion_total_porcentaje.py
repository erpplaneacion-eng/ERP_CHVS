# Generated manually 2026-02-12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nutricion', '0011_renombrar_tabla_requerimientos_nutricionales'),
        ('principal', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdecuacionTotalPorcentaje',
            fields=[
                ('id_adecuacion_porcentaje', models.CharField(max_length=50, primary_key=True, serialize=False, verbose_name='ID Adecuación Porcentaje')),
                ('calorias_porc', models.DecimalField(decimal_places=1, max_digits=5, verbose_name='Calorías (%)')),
                ('proteina_porc', models.DecimalField(decimal_places=1, max_digits=5, verbose_name='Proteína (%)')),
                ('grasa_porc', models.DecimalField(decimal_places=1, max_digits=5, verbose_name='Grasa (%)')),
                ('cho_porc', models.DecimalField(decimal_places=1, max_digits=5, verbose_name='CHO (%)')),
                ('calcio_porc', models.DecimalField(decimal_places=1, max_digits=5, verbose_name='Calcio (%)')),
                ('hierro_porc', models.DecimalField(decimal_places=1, max_digits=5, verbose_name='Hierro (%)')),
                ('sodio_porc', models.DecimalField(decimal_places=1, max_digits=5, verbose_name='Sodio (%)')),
                ('id_nivel_escolar_uapa', models.ForeignKey(db_column='id_nivel_escolar_uapa', on_delete=django.db.models.deletion.PROTECT, related_name='adecuaciones_porcentaje', to='principal.tablagradosescolaresUapa', verbose_name='Nivel Escolar UAPA')),
                ('id_modalidad', models.ForeignKey(blank=True, db_column='id_modalidad', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='adecuaciones_porcentaje', to='nutricion.modalidadesdeconsumo', verbose_name='Modalidad de Consumo')),
            ],
            options={
                'verbose_name': 'Adecuación Total Porcentaje',
                'verbose_name_plural': 'Adecuaciones Totales Porcentaje',
                'db_table': 'nutricion_adecuacion_total_porc',
                'ordering': ['id_nivel_escolar_uapa', 'id_modalidad'],
                'unique_together': {('id_nivel_escolar_uapa', 'id_modalidad')},
            },
        ),
    ]
