# Generated manually for PlanificacionRaciones model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('planeacion', '0010_programa_municipio'),
        ('principal', '0008_nivelgradoescolar'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanificacionRaciones',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('focalizacion', models.CharField(max_length=10, verbose_name='Focalización')),
                ('ano', models.IntegerField(default=2025, verbose_name='Año')),
                ('cap_am', models.IntegerField(default=0, verbose_name='CAP AM (Complemento Alimentario Preparado AM)')),
                ('cap_pm', models.IntegerField(default=0, verbose_name='CAP PM (Complemento Alimentario Preparado PM)')),
                ('almuerzo_ju', models.IntegerField(default=0, verbose_name='Almuerzo Jornada Única')),
                ('refuerzo', models.IntegerField(default=0, verbose_name='Refuerzo Complemento AM/PM')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')),
                ('etc', models.ForeignKey(db_column='id_municipio', on_delete=django.db.models.deletion.PROTECT, to='principal.principalmunicipio', verbose_name='ETC (Municipio)')),
                ('nivel_escolar', models.ForeignKey(db_column='id_nivel_grado', on_delete=django.db.models.deletion.PROTECT, to='principal.nivelgradoescolar', verbose_name='Nivel Escolar')),
                ('sede_educativa', models.ForeignKey(db_column='cod_interprise', on_delete=django.db.models.deletion.PROTECT, to='planeacion.sedeseducativas', verbose_name='Sede Educativa')),
            ],
            options={
                'verbose_name': 'Planificación de Raciones',
                'verbose_name_plural': 'Planificaciones de Raciones',
                'db_table': 'planificacion_raciones',
                'ordering': ['etc__nombre_municipio', 'focalizacion', 'sede_educativa__nombre_sede_educativa'],
                'unique_together': {('etc', 'focalizacion', 'sede_educativa', 'nivel_escolar', 'ano')},
                'indexes': [
                    models.Index(fields=['etc', 'focalizacion', 'ano'], name='planificaci_etc_id_8e7a3d_idx'),
                    models.Index(fields=['sede_educativa'], name='planificaci_cod_int_7f1c5e_idx'),
                ],
            },
        ),
    ]
