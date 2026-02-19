from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Crea las tablas para sub-restricciones de alimentos por subgrupo dentro de una modalidad.
    Permite exigir que ciertas apariciones de un grupo usen alimentos de una lista blanca.
    """

    dependencies = [
        ('nutricion', '0025_grupo_excluyente_set'),
        ('principal', '0003_registroactividad'),
    ]

    operations = [
        migrations.CreateModel(
            name='RestriccionAlimentoSubgrupo',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(
                    max_length=120,
                    verbose_name='Nombre de la Sub-restricción',
                    help_text="Ej: 'G4 Leguminosas', 'G4 Huevo obligatorio'"
                )),
                ('frecuencia', models.IntegerField(
                    verbose_name='Frecuencia Requerida',
                    help_text='Cuántas veces por semana debe usarse un alimento de la lista blanca'
                )),
                ('modalidad', models.ForeignKey(
                    db_column='id_modalidades',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='restricciones_subgrupo',
                    to='principal.modalidadesdeconsumo',
                    verbose_name='Modalidad de Consumo'
                )),
                ('grupo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='restricciones_subgrupo',
                    to='nutricion.gruposalimentos',
                    verbose_name='Grupo de Alimentos'
                )),
            ],
            options={
                'verbose_name': 'Sub-restricción de Alimento',
                'verbose_name_plural': 'Sub-restricciones de Alimentos',
                'db_table': 'nutricion_restriccion_alimento_subgrupo',
                'ordering': ['modalidad', 'grupo', 'nombre'],
            },
        ),
        migrations.CreateModel(
            name='RestriccionAlimentoEspecifico',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
                ('restriccion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='alimentos',
                    to='nutricion.restriccionalimentosubgrupo',
                    verbose_name='Sub-restricción'
                )),
                ('alimento', models.ForeignKey(
                    db_column='codigo_alimento',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='restricciones_subgrupo',
                    to='nutricion.tablaalimentos2018icbf',
                    to_field='codigo',
                    verbose_name='Alimento ICBF'
                )),
            ],
            options={
                'verbose_name': 'Alimento de Sub-restricción',
                'verbose_name_plural': 'Alimentos de Sub-restricciones',
                'db_table': 'nutricion_restriccion_alimento_especifico',
            },
        ),
        migrations.AlterUniqueTogether(
            name='restriccionalimentoespecifico',
            unique_together={('restriccion', 'alimento')},
        ),
    ]
