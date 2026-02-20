from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Crea la tabla nutricion_recomendacion_diaria_por_grado_mod.
    Almacena las recomendaciones nutricionales diarias oficiales ICBF
    por nivel escolar y modalidad de consumo.
    Se usa como denominador para calcular el porcentaje de adecuación del menú.
    """

    dependencies = [
        ('nutricion', '0026_restriccion_alimento_subgrupo'),
        ('principal', '0003_registroactividad'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecomendacionDiariaGradoMod',
            fields=[
                ('id_calorias_nivel_escolar', models.CharField(
                    max_length=20,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID Recomendación'
                )),
                ('calorias_kcal', models.DecimalField(
                    decimal_places=1, max_digits=8,
                    verbose_name='Calorías (kcal)'
                )),
                ('proteina_g', models.DecimalField(
                    decimal_places=1, max_digits=7,
                    verbose_name='Proteína (g)'
                )),
                ('grasa_g', models.DecimalField(
                    decimal_places=1, max_digits=7,
                    verbose_name='Grasa (g)'
                )),
                ('cho_g', models.DecimalField(
                    decimal_places=1, max_digits=8,
                    verbose_name='CHO (g)'
                )),
                ('calcio_mg', models.DecimalField(
                    decimal_places=1, max_digits=8,
                    verbose_name='Calcio (mg)'
                )),
                ('hierro_mg', models.DecimalField(
                    decimal_places=1, max_digits=6,
                    verbose_name='Hierro (mg)'
                )),
                ('sodio_mg', models.DecimalField(
                    decimal_places=1, max_digits=8,
                    verbose_name='Sodio (mg)'
                )),
                ('nivel_escolar_uapa', models.ForeignKey(
                    db_column='nivel_escolar_uapa',
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='recomendaciones_diarias',
                    to='principal.tablagradosescolaresuapa',
                    verbose_name='Nivel Escolar'
                )),
                ('id_modalidades', models.ForeignKey(
                    db_column='id_modalidades',
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='recomendaciones_diarias',
                    to='principal.modalidadesdeconsumo',
                    verbose_name='Modalidad'
                )),
            ],
            options={
                'verbose_name': 'Recomendación Diaria por Grado y Modalidad',
                'verbose_name_plural': 'Recomendaciones Diarias por Grado y Modalidad',
                'db_table': 'nutricion_recomendacion_diaria_por_grado_mod',
            },
        ),
        migrations.AlterUniqueTogether(
            name='recomendaciondiariagradomod',
            unique_together={('nivel_escolar_uapa', 'id_modalidades')},
        ),
    ]
